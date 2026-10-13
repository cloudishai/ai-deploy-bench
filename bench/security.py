"""Independent security review of a deployment, by a separate Claude Code session.

While the deployment is still live, the reviewer gets a read-only copy of what the agent produced,
condensed transcripts of the build and deploy sessions, the resources the benchmark found and the
public URL. It has no cloud credentials. It scores the fixed rubric in benchmark.yaml with evidence,
and the harness turns those scores into a 0-100 score, so the weighting isn't left to the model.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from bench import agent, codestats
from bench.prompts import TEMPLATES
from bench.redact import redact_text, redact_tree

if TYPE_CHECKING:
    from bench.cell import Cell

RESULT_FILE = "security-review.json"
SEVERITIES = ("critical", "high", "medium", "low", "info")
MAX_RESULT_CHARS = 1500
MAX_INPUT_CHARS = 4000
FENCE = "````"


def condensed_transcript(path: Path) -> str:
    """The agent's messages, tool calls and abbreviated tool results, as markdown."""
    if not path.exists():
        return "No transcript: this phase didn't run.\n"
    lines = []
    with path.open(errors="ignore") as events:
        for raw in events:
            try:
                event = json.loads(raw).get("e") or {}
            except (ValueError, AttributeError):
                continue
            content = (event.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if event.get("type") == "assistant" and block.get("type") == "text" and block.get("text", "").strip():
                    lines.append(f"**Agent:** {block['text'].strip()}\n")
                elif event.get("type") == "assistant" and block.get("type") == "tool_use":
                    payload = json.dumps(block.get("input") or {}, indent=1)[:MAX_INPUT_CHARS]
                    lines.append(f"**Tool call: {block.get('name')}**\n{FENCE}\n{payload}\n{FENCE}\n")
                elif event.get("type") == "user" and block.get("type") == "tool_result":
                    inner = block.get("content")
                    if isinstance(inner, list):
                        inner = "\n".join(b.get("text", "") for b in inner if isinstance(b, dict))
                    text = str(inner or "")
                    clipped = text[:MAX_RESULT_CHARS] + (f"\n... ({len(text) - MAX_RESULT_CHARS} more characters)"
                                                         if len(text) > MAX_RESULT_CHARS else "")
                    label = "Result (error)" if block.get("is_error") else "Result"
                    lines.append(f"{label}:\n{FENCE}\n{clipped}\n{FENCE}\n")
    return "\n".join(lines) or "The transcript has no messages.\n"


def prepare(cell: "Cell", directory: Path, secrets: list[str]) -> None:
    """Lays out what the reviewer reads: app/, process/ and TASK.md."""
    if directory.exists():
        shutil.rmtree(directory)
    app = directory / "app"
    app.mkdir(parents=True)
    if cell.workspace.exists():
        for path in codestats.source_files(cell.workspace, set()):
            if path.stat().st_size <= codestats.MAX_SNAPSHOT_FILE:
                target = app / path.relative_to(cell.workspace)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    redact_tree(app, secrets)
    process = directory / "process"
    process.mkdir()
    for phase in ("build", "deploy"):
        (process / f"{phase}.md").write_text(condensed_transcript(cell.dir / phase / "transcript.jsonl"))
    (process / "deployment.json").write_text(json.dumps(cell.deployment(), indent=2))
    inventory = cell.read("inventory.json") or {}
    resources = [{k: r.get(k) for k in ("kind", "name", "plan", "url", "details")}
                 for role in inventory.values() if isinstance(role, dict) for r in role.get("resources", [])]
    (process / "resources.json").write_text(json.dumps(resources, indent=2, default=str))
    (directory / "TASK.md").write_text(cell.config.app(cell.info["app"]).task)


def render_prompt(cell: "Cell", url: str) -> str:
    rubric = cell.config.security_rubric
    lines = "\n".join(f"- `{c['id']}` ({c['name']}, weight {c['weight']}): {c['question']}" for c in rubric)
    return (TEMPLATES / "review.md").read_text().format(
        cloud_name=cell.config.cloud(cell.info["cloud"]).name,
        url=url,
        rubric=lines,
        criterion_ids=", ".join(f"`{c['id']}`" for c in rubric),
    )


def score(rubric: tuple[dict[str, Any], ...], review: Any) -> tuple[float | None, list[dict[str, Any]], list[str]]:
    """Validates the reviewer's criteria; returns (0-100 score, criteria rows, problems)."""
    criteria = review.get("criteria") if isinstance(review, dict) else None
    if not isinstance(criteria, dict):
        return None, [], ["no criteria object"]
    rows, problems, weighted = [], [], 0.0
    for item in rubric:
        entry = criteria.get(item["id"]) if isinstance(criteria.get(item["id"]), dict) else {}
        value = entry.get("score")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 10:
            problems.append(f"missing or invalid score for {item['id']}")
            continue
        weighted += item["weight"] * value / 10
        rows.append({"id": item["id"], "name": item["name"], "weight": item["weight"], "score": value,
                     "rationale": str(entry.get("rationale") or "")[:600]})
    if problems:
        return None, rows, problems
    return round(100 * weighted / sum(item["weight"] for item in rubric), 1), rows, []


def findings(review: dict[str, Any]) -> list[dict[str, str]]:
    found = []
    for item in review.get("findings") or []:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity") or "info").lower()
        found.append({
            "severity": severity if severity in SEVERITIES else "info",
            "criterion": str(item.get("criterion") or ""),
            "title": str(item.get("title") or "")[:200],
            "evidence": str(item.get("evidence") or "")[:800],
            "recommendation": str(item.get("recommendation") or "")[:500],
        })
    return sorted(found, key=lambda f: SEVERITIES.index(f["severity"]))


def run(cell: "Cell", env: dict[str, str], secrets: list[str], claude: str, log: Callable[[str], None]) -> dict[str, Any]:
    verification = cell.read("verify.json") or {}
    url = verification.get("url")
    if not (url and (verification.get("readiness") or {}).get("ready")):
        return {"status": "skipped", "detail": "no reachable deployment to review"}
    cfg = cell.config
    reviewer = cfg.reviewer
    directory = cell.workspace.parent / f"{cell.prefix}-review"
    prepare(cell, directory, secrets)
    phase = agent.run_phase(
        name="review",
        prompt=render_prompt(cell, url),
        cwd=directory,
        model=reviewer["model"],
        effort=reviewer.get("effort"),
        out_dir=cell.dir / "review",
        timeout_s=reviewer.get("timeout_minutes", 20) * 60,
        session_id=str(uuid.uuid4()),
        max_budget_usd=reviewer.get("max_budget_usd"),
        env=env,
        prices=cfg.model_prices,
        secrets=secrets,
        claude=claude,
        log=log,
    )
    report: dict[str, Any] = {"reviewer": {
        "model": reviewer["model"], "effort": reviewer.get("effort"), "hipaa": bool(reviewer.get("hipaa")),
        "status": phase.status,
        "wall_time_s": phase.wall_time_s, "tokens": phase.tokens.get("total"), "cost_usd": phase.cost_usd,
    }}
    result = directory / RESULT_FILE
    if not result.exists():
        return {**report, "status": "error", "detail": f"the reviewer didn't write {RESULT_FILE} ({phase.status})"}
    try:
        review = json.loads(redact_text(result.read_text(), secrets))
    except ValueError as error:
        return {**report, "status": "error", "detail": f"{RESULT_FILE} isn't valid JSON: {error}"}
    value, rows, problems = score(cfg.security_rubric, review)
    if problems:
        return {**report, "status": "error", "detail": "; ".join(problems), "criteria": rows}
    return {**report, "status": "completed", "score": value, "criteria": rows, "findings": findings(review),
            "summary": str(review.get("summary") or "")[:1500]}
