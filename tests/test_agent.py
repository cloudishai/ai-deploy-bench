"""Tests the Claude Code runner against a fake `claude` that replays recorded stream-json."""

import sys
import textwrap
import time
from pathlib import Path

import pytest

from bench import agent

FIXTURES = Path(__file__).parent / "fixtures" / "stream"
PRICES = {"claude-haiku-5-5": {"input": 0.10, "cache_write": 0.125, "cache_read": 0.01, "output": 0.50}}
SESSION = "59cafd68-f9d6-46e0-98dc-c9671a64d54c"


@pytest.fixture
def fake_claude(tmp_path):
    """Writes an executable that prints a fixture stream, then optionally hangs."""

    def make(stream: str, hang_after: int | None = None, hang_seconds: float = 60) -> str:
        script = tmp_path / f"claude-{stream}-{hang_after}"
        script.write_text(textwrap.dedent(f"""\
            #!{sys.executable}
            import sys, time
            sys.stdin.read()
            lines = open({str(FIXTURES / (stream + '.jsonl'))!r}).read().splitlines()
            for i, line in enumerate(lines):
                if {hang_after!r} is not None and i == {hang_after!r}:
                    time.sleep({hang_seconds})
                print(line, flush=True)
            if {hang_after!r} is not None and {hang_after!r} >= len(lines):
                time.sleep({hang_seconds})
            """))
        script.chmod(0o755)
        return str(script)

    return make


def run(claude: str, tmp_path: Path, **kwargs) -> agent.Phase:
    defaults = dict(
        name="build", prompt="do it", cwd=tmp_path, model="claude-haiku-5-5", out_dir=tmp_path / "out",
        timeout_s=30, session_id=SESSION, prices=PRICES, claude=claude, log=lambda _: None,
    )
    return agent.run_phase(**(defaults | kwargs))


def test_first_phase_uses_session_totals(fake_claude, tmp_path):
    phase = run(fake_claude("phase1"), tmp_path)
    assert phase.status == "completed" and phase.started
    assert phase.tokens == {"input": 3113, "output": 91, "cache_read": 27754, "cache_write": 30909, "total": 61867}
    assert phase.cost_usd == pytest.approx(0.004498, abs=1e-6)
    assert phase.cost_source == "claude-code"
    assert phase.tool_calls == {"Bash": 1}
    assert phase.commands[0]["command"].startswith("echo phase-one-ok")
    assert phase.turns == 2
    assert phase.model == "claude-haiku-5-5"
    assert (tmp_path / "out" / "transcript.jsonl").read_text().count("\n") == 5


def test_resumed_phase_subtracts_previous_totals(fake_claude, tmp_path):
    build = run(fake_claude("phase1"), tmp_path)
    deploy = run(fake_claude("phase2"), tmp_path, name="deploy", resume=True, previous=build.cumulative,
                 out_dir=tmp_path / "deploy")
    assert deploy.tokens == {"input": 107, "output": 92, "cache_read": 61901, "cache_write": 228, "total": 62328}
    assert deploy.cost_usd == pytest.approx(0.005202175 - 0.004497965, abs=1e-6)
    assert deploy.cost_source == "claude-code"


def test_resumed_phase_without_previous_totals_estimates(fake_claude, tmp_path):
    deploy = run(fake_claude("phase2"), tmp_path, name="deploy", resume=True, previous=None)
    assert deploy.tokens["input"] == 107 and deploy.tokens["cache_read"] == 61901
    assert deploy.cost_source == "estimated"
    assert deploy.cost_usd == pytest.approx(agent.estimate_cost(deploy.tokens, PRICES["claude-haiku-5-5"]))


def test_timeout_stops_the_agent_and_estimates_usage(fake_claude, tmp_path):
    start = time.monotonic()
    phase = run(fake_claude("phase1", hang_after=2), tmp_path, timeout_s=2)
    assert time.monotonic() - start < 25
    assert phase.status == "timeout"
    assert phase.tokens_estimated and phase.cost_source == "estimated"
    assert phase.tokens["input"] == 3059  # only the first API call was streamed
    assert phase.started


def test_process_lingering_after_result_is_stopped(fake_claude, tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "RESULT_GRACE_S", 1)
    phase = run(fake_claude("phase1", hang_after=99), tmp_path)
    assert phase.status == "completed"
    assert phase.lingered
    assert phase.wall_time_s < 5 and phase.exit_time_s < 25


def test_crash_without_output(tmp_path):
    script = tmp_path / "claude-crash"
    script.write_text(f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nsys.exit(3)\n")
    script.chmod(0o755)
    phase = run(str(script), tmp_path)
    assert phase.status == "crashed"
    assert not phase.started
    assert phase.exit_code == 3


def test_missing_binary_is_a_crash(tmp_path):
    phase = run(str(tmp_path / "does-not-exist"), tmp_path)
    assert phase.status == "crashed" and "could not start" in phase.detail
    assert (tmp_path / "out" / "phase.json").exists()


def test_invalid_utf8_and_orphaned_children_do_not_hang(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EXIT_DRAIN_S", 1)
    script = tmp_path / "claude-orphan"
    script.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import subprocess, sys
        sys.stdin.read()
        # A background child that inherits stdout and outlives Claude Code.
        subprocess.Popen(["sleep", "30"])
        sys.stdout.buffer.write(b"\\xff\\xfe not utf-8\\n")
        sys.stdout.write(open({str(FIXTURES / "phase1.jsonl")!r}).read())
        sys.stdout.flush()
        """))
    script.chmod(0o755)
    start = time.monotonic()
    phase = run(str(script), tmp_path)
    assert time.monotonic() - start < 15
    assert phase.status == "completed"
    assert '"raw"' in (tmp_path / "out" / "transcript.jsonl").read_text()


def test_cancelling_the_step_stops_claude_code(fake_claude, tmp_path):
    import os
    import signal
    import threading

    pid_seen = []

    def cancel_soon():
        time.sleep(1.5)
        pid_seen.append(int((tmp_path / "out" / "agent.pid").read_text()))
        os.kill(os.getpid(), signal.SIGTERM)  # what the runner does when a run is cancelled

    threading.Thread(target=cancel_soon, daemon=True).start()
    start = time.monotonic()
    phase = run(fake_claude("phase1", hang_after=2, hang_seconds=60), tmp_path)
    assert time.monotonic() - start < 15
    assert phase.status == "cancelled" and "SIGTERM" in phase.detail
    assert (tmp_path / "out" / "phase.json").exists()
    with pytest.raises(ProcessLookupError):
        os.killpg(pid_seen[0], 0)  # the whole process group is gone
