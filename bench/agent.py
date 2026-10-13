"""Runs one Claude Code phase headlessly and turns its stream-json output into metrics.

Stream facts this relies on (checked against Claude Code 2.1.296):
- `assistant` events repeat once per content block with the same `message.id`, each carrying
  that API call's usage; per-message `output_tokens` are placeholders.
- The `result` event has the real totals. On `--resume`, its `usage`, `num_turns` and
  `duration_ms` cover only that invocation, while `total_cost_usd`, `modelUsage` and
  `duration_api_ms` are cumulative for the whole session. `--max-budget-usd` applies per
  invocation.
- After the result, `claude -p` keeps running until background commands it started exit, so
  phase time is measured up to the result event and the process is stopped shortly after.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import queue
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from bench.redact import redact_text

TOKEN_KEYS = ("input", "output", "cache_read", "cache_write")
MODEL_USAGE_KEYS = {
    "input": "inputTokens",
    "output": "outputTokens",
    "cache_read": "cacheReadInputTokens",
    "cache_write": "cacheCreationInputTokens",
}
RESULT_GRACE_S = 20
# After Claude Code exits, an orphaned child can keep stdout open; stop reading after this long.
EXIT_DRAIN_S = 10
MAX_COMMANDS = 400


@dataclasses.dataclass
class Phase:
    name: str
    status: str = "not_run"  # completed | error | timeout | crashed | cancelled | not_run
    detail: str = ""
    session_id: str | None = None
    started: bool = False  # Claude Code emitted its init event, so the session can be resumed
    resumed: bool = False
    started_at: str | None = None
    wall_time_s: float | None = None  # start to result event (or to the kill on timeout)
    exit_time_s: float | None = None  # start to process exit
    api_time_s: float | None = None
    turns: int | None = None
    tokens: dict[str, int] = dataclasses.field(default_factory=dict)
    tokens_estimated: bool = False
    cost_usd: float | None = None
    cost_source: str = ""  # claude-code | estimated
    model_usage: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    cumulative: dict[str, Any] | None = None  # session totals as reported, for diffing the next phase
    tool_calls: dict[str, int] = dataclasses.field(default_factory=dict)
    tool_errors: int = 0
    subagent_tool_calls: int = 0
    commands: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    compactions: int = 0
    api_retries: int = 0
    result_subtype: str | None = None
    stop_reason: str | None = None
    terminal_reason: str | None = None
    permission_denials: int = 0
    final_message: str = ""
    model: str | None = None
    claude_code_version: str | None = None
    api_key_source: str | None = None
    exit_code: int | None = None
    lingered: bool = False  # still running after the result (background commands) and was stopped

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Phase":
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class StreamParser:
    """Accumulates metrics from stream-json events; `feed` returns a live-log line or None."""

    def __init__(self, phase: Phase) -> None:
        self.phase = phase
        self.result: dict[str, Any] | None = None
        self.result_at: float | None = None
        self.timed_out = False
        self.last_text = ""
        self.usage_by_message: dict[str, dict[str, int]] = {}
        self.pending: dict[str, dict[str, Any]] = {}  # tool_use_id -> command entry

    def feed(self, t: float, event: dict[str, Any]) -> str | None:
        kind, subtype = event.get("type"), event.get("subtype")
        if kind == "system" and subtype == "init":
            self.phase.started = True
            self.phase.session_id = event.get("session_id") or self.phase.session_id
            self.phase.model = event.get("model")
            self.phase.claude_code_version = event.get("claude_code_version")
            self.phase.api_key_source = event.get("apiKeySource")
            return f"session {self.phase.session_id} ({self.phase.model}, Claude Code {self.phase.claude_code_version})"
        if kind == "system" and subtype == "compact_boundary":
            self.phase.compactions += 1
            return "context compacted"
        if kind == "system" and subtype == "api_retry":
            self.phase.api_retries += 1
            return f"API retry {event.get('attempt')}: {event.get('error_status') or event.get('error')}"
        if kind == "assistant":
            return self._assistant(t, event)
        if kind == "user":
            self._tool_results(event)
            return None
        if kind == "result":
            self.result = event
            return f"result: {event.get('subtype')} after {event.get('num_turns')} turns"
        return None

    def _assistant(self, t: float, event: dict[str, Any]) -> str | None:
        message = event.get("message") or {}
        usage = message.get("usage") or {}
        if message.get("id") and usage:
            self.usage_by_message[message["id"]] = {
                "input": usage.get("input_tokens") or 0,
                "output": usage.get("output_tokens") or 0,
                "cache_read": usage.get("cache_read_input_tokens") or 0,
                "cache_write": usage.get("cache_creation_input_tokens") or 0,
            }
        lines = []
        for block in message.get("content") or []:
            if block.get("type") == "text" and block.get("text", "").strip():
                self.last_text = block["text"]
            elif block.get("type") == "tool_use":
                name = block.get("name", "?")
                tool_input = block.get("input") or {}
                self.phase.tool_calls[name] = self.phase.tool_calls.get(name, 0) + 1
                if event.get("parent_tool_use_id"):
                    self.phase.subagent_tool_calls += 1
                if name == "Bash" and len(self.phase.commands) < MAX_COMMANDS:
                    entry = {"t": round(t, 1), "command": str(tool_input.get("command", ""))[:2000], "error": False}
                    self.phase.commands.append(entry)
                    self.pending[block.get("id", "")] = entry
                lines.append(f"{name}: {describe_tool(name, tool_input)}")
        return "\n".join(lines) or None

    def _tool_results(self, event: dict[str, Any]) -> None:
        content = (event.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_result" and block.get("is_error"):
                self.phase.tool_errors += 1
                if entry := self.pending.get(block.get("tool_use_id", "")):
                    entry["error"] = True


def describe_tool(name: str, tool_input: dict[str, Any]) -> str:
    for key in ("command", "file_path", "url", "query", "description", "pattern", "prompt"):
        if value := tool_input.get(key):
            first_line = str(value).strip().splitlines()[0] if str(value).strip() else ""
            return first_line[:160]
    return ""


def normalize_model_usage(raw: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    usage = {}
    for model, values in (raw or {}).items():
        entry = {key: int(values.get(field) or 0) for key, field in MODEL_USAGE_KEYS.items()}
        entry["cost_usd"] = float(values.get("costUSD") or 0.0)
        entry["web_searches"] = int(values.get("webSearchRequests") or 0)
        usage[model] = entry
    return usage


def diff_model_usage(current: dict[str, dict], previous: dict[str, dict]) -> dict[str, dict] | None:
    """Per-phase usage from two cumulative snapshots; None if the snapshots are inconsistent."""
    result = {}
    for model, values in current.items():
        before = previous.get(model, {})
        delta = {key: values.get(key, 0) - before.get(key, 0) for key in values}
        if any(v < -1e-9 for v in delta.values()):
            return None
        if any(delta.values()):
            result[model] = delta
    return result


def total_tokens(per_model: dict[str, dict]) -> dict[str, int]:
    tokens = {key: sum(int(v.get(key, 0)) for v in per_model.values()) for key in TOKEN_KEYS}
    tokens["total"] = sum(tokens.values())
    return tokens


def estimate_cost(tokens: dict[str, int], prices: dict[str, float] | None) -> float | None:
    if not prices:
        return None
    return round(sum(tokens.get(key, 0) * prices.get(key, 0.0) for key in TOKEN_KEYS) / 1_000_000, 6)


def apply_usage(phase: Phase, parser: StreamParser, previous: dict[str, Any] | None, prices: dict[str, dict]) -> None:
    model_prices = prices.get(phase.model or "", None)
    result = parser.result
    if result:
        cumulative = {
            "cost_usd": float(result.get("total_cost_usd") or 0.0),
            "model_usage": normalize_model_usage(result.get("modelUsage")),
            "api_ms": int(result.get("duration_api_ms") or 0),
        }
        phase.cumulative = cumulative
        per_model = cumulative["model_usage"]
        cost = cumulative["cost_usd"]
        phase.api_time_s = round(cumulative["api_ms"] / 1000, 1)
        if phase.resumed:
            per_model = diff_model_usage(cumulative["model_usage"], previous["model_usage"]) if previous else None
            cost = cumulative["cost_usd"] - previous["cost_usd"] if previous else None
            api_ms = cumulative["api_ms"] - previous.get("api_ms", 0) if previous else -1
            phase.api_time_s = round(api_ms / 1000, 1) if api_ms >= 0 else None
        if per_model is not None and cost is not None and cost >= -1e-9:
            phase.model_usage = per_model
            phase.tokens = total_tokens(per_model)
            phase.cost_usd, phase.cost_source = round(max(cost, 0.0), 6), "claude-code"
            return
        # The previous phase's totals are unknown, so fall back to this invocation's own usage.
        usage = result.get("usage") or {}
        phase.tokens = total_tokens({"": {
            "input": usage.get("input_tokens") or 0,
            "output": usage.get("output_tokens") or 0,
            "cache_read": usage.get("cache_read_input_tokens") or 0,
            "cache_write": usage.get("cache_creation_input_tokens") or 0,
        }})
    else:
        # No result event (timeout or crash): per-message usage undercounts output tokens.
        phase.tokens = total_tokens(parser.usage_by_message)
        phase.tokens_estimated = True
    phase.cost_usd, phase.cost_source = estimate_cost(phase.tokens, model_prices), "estimated"


class Cancelled(Exception):
    """The step itself was asked to stop (workflow cancelled or step timeout)."""


def _cancel(signum: int, _frame: Any) -> None:
    raise Cancelled(signal.Signals(signum).name)


def stop_process_group(proc: subprocess.Popen, patient: bool = True) -> None:
    """Stops Claude Code and everything it started; impatient when the runner is cancelling us."""
    steps = ((signal.SIGINT, 15), (signal.SIGTERM, 10), (signal.SIGKILL, 5)) if patient else \
        ((signal.SIGTERM, 2), (signal.SIGKILL, 2))
    for sig, wait in steps:
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(wait)
            return
        except subprocess.TimeoutExpired:
            continue


def run_phase(
    *,
    name: str,
    prompt: str,
    cwd: Path,
    model: str,
    out_dir: Path,
    timeout_s: float,
    session_id: str,
    resume: bool = False,
    previous: dict[str, Any] | None = None,
    effort: str | None = None,
    max_budget_usd: float | None = None,
    env: dict[str, str] | None = None,
    prices: dict[str, dict] | None = None,
    secrets: list[str] | None = None,
    claude: str = "claude",
    log: Callable[[str], None] = print,
) -> Phase:
    out_dir.mkdir(parents=True, exist_ok=True)
    command = [claude, "-p", "--output-format", "stream-json", "--verbose", "--model", model,
               "--permission-mode", "bypassPermissions"]
    command += ["--resume", session_id] if resume else ["--session-id", session_id]
    if effort:
        command += ["--effort", effort]
    if max_budget_usd:
        command += ["--max-budget-usd", str(max_budget_usd)]

    phase = Phase(name=name, session_id=session_id, resumed=resume, model=model)
    phase.started_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    parser = StreamParser(phase)
    start = time.monotonic()
    # The prompt goes through stdin: variadic flags such as --allowedTools would swallow a positional one.
    with (out_dir / "stderr.log").open("w") as stderr, (out_dir / "transcript.jsonl").open("w") as transcript:
        try:
            proc = subprocess.Popen(
                command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                text=True, encoding="utf-8", errors="replace", bufsize=1, start_new_session=True,
            )
        except OSError as error:
            phase.status, phase.detail = "crashed", f"could not start Claude Code: {error}"
            (out_dir / "phase.json").write_text(json.dumps(phase.to_dict(), indent=2))
            return phase
        (out_dir / "agent.pid").write_text(str(proc.pid))  # lets teardown kill survivors of a cancelled step
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except BrokenPipeError:
            pass  # exited before reading the prompt; the exit code tells the story

        lines: queue.Queue = queue.Queue()

        def read() -> None:
            try:
                for line in proc.stdout:
                    lines.put((time.monotonic(), line))
            finally:
                lines.put(None)

        threading.Thread(target=read, daemon=True).start()
        cancelled = None
        # The runner signals the step when a run is cancelled or the step times out. Claude Code runs
        # in its own session, so stop it here or it would keep deploying while teardown runs.
        handlers = {}
        if threading.current_thread() is threading.main_thread():
            handlers = {sig: signal.signal(sig, _cancel) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            stream(lines, proc, phase, parser, transcript, secrets or [], name, log, start, start + timeout_s, timeout_s)
        except Cancelled as reason:
            cancelled = str(reason)
        finally:
            for sig in handlers:  # finish cleaning up even if the runner signals again
                signal.signal(sig, signal.SIG_IGN)
        if cancelled:
            log(f"[{name}] step cancelled ({cancelled}), stopping Claude Code")
            stop_process_group(proc, patient=False)
        result_at, timed_out = parser.result_at, parser.timed_out
        proc.wait()
        # Leftover background processes from the session (dev servers and the like) go too.
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    end = time.monotonic()
    phase.exit_code = proc.returncode
    phase.exit_time_s = round(end - start, 1)
    phase.wall_time_s = round((result_at or end) - start, 1)
    result = parser.result
    if result:
        phase.result_subtype = result.get("subtype")
        phase.status = "completed" if result.get("subtype") == "success" and not result.get("is_error") else "error"
        failure = str(result.get("result") or "")[:300] if result.get("is_error") else ""
        phase.detail = "; ".join(result.get("errors") or []) or failure or (result.get("subtype") or "")
        phase.turns = result.get("num_turns")
        phase.stop_reason = result.get("stop_reason")
        phase.terminal_reason = result.get("terminal_reason")
        phase.permission_denials = len(result.get("permission_denials") or [])
        phase.final_message = str(result.get("result") or parser.last_text)[:6000]
    else:
        phase.status = "cancelled" if cancelled else "timeout" if timed_out else "crashed"
        phase.detail = f"no result event; exit code {proc.returncode}" + (f"; step cancelled by {cancelled}" if cancelled else "")
        phase.final_message = parser.last_text[:6000]
    apply_usage(phase, parser, previous, prices or {})
    (out_dir / "phase.json").write_text(json.dumps(phase.to_dict(), indent=2))
    for sig, handler in handlers.items():
        signal.signal(sig, handler)
    return phase


def stream(lines: queue.Queue, proc: subprocess.Popen, phase: Phase, parser: StreamParser, transcript: Any,
           secrets: list[str], name: str, log: Callable[[str], None], start: float, deadline: float,
           timeout_s: float) -> None:
    """Consumes Claude Code's output until it ends, enforcing the time limit."""
    exited_at = None
    while True:
        now = time.monotonic()
        if parser.result_at is None and now > deadline and not parser.timed_out:
            parser.timed_out = True
            log(f"[{name}] timeout after {timeout_s / 60:.0f} min, stopping Claude Code")
            threading.Thread(target=stop_process_group, args=(proc,), daemon=True).start()
        if parser.result_at is not None and now > parser.result_at + RESULT_GRACE_S and proc.poll() is None \
                and not phase.lingered:
            phase.lingered = True
            threading.Thread(target=stop_process_group, args=(proc,), daemon=True).start()
        if proc.poll() is not None:
            exited_at = exited_at or now
            if now - exited_at > EXIT_DRAIN_S and lines.empty():
                return
        try:
            item = lines.get(timeout=1.0)
        except queue.Empty:
            continue
        if item is None:
            return
        received, line = item
        elapsed = received - start
        # Mask secrets and token-shaped strings before anything is stored or truncated.
        line = redact_text(line, secrets)
        try:
            event = json.loads(line)
        except ValueError:
            transcript.write(json.dumps({"t": round(elapsed, 3), "raw": line.rstrip("\n")}) + "\n")
            continue
        transcript.write(json.dumps({"t": round(elapsed, 3), "e": event}) + "\n")
        message = parser.feed(elapsed, event) if isinstance(event, dict) else None
        if message:
            stamp = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
            for text in message.splitlines():
                log(f"[{name} {stamp}] {text}")
        if parser.result is not None and parser.result_at is None:
            parser.result_at = received

