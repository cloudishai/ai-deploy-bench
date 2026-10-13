"""Collects cell results into results/runs/<run>/, rebuilds the run index and refreshes README.md."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any, Iterable

from bench import config, fmt

README_START, README_END = "<!-- results:start -->", "<!-- results:end -->"
SUMMARY_FIELDS = (
    "cloud", "model", "app", "trial", "status", "failure_stage", "score", "checks_passed", "checks_total",
    "required_failed", "url",
)


def cell_key(cell: dict[str, Any]) -> tuple[str, str, str, int]:
    return cell["model"], cell["cloud"], cell["app"], int(cell["trial"])


def cell_path(cell: dict[str, Any]) -> str:
    return f"cells/{cell['model']}/{cell['cloud']}/{cell['app']}-t{cell['trial']}"


def load_results(artifacts: Path) -> dict[tuple, tuple[dict[str, Any], Path]]:
    found = {}
    for path in sorted(artifacts.rglob("result.json")):
        try:
            record = json.loads(path.read_text())
        except ValueError:
            continue
        found[cell_key(record)] = (record, path.parent)
    return found


def compact(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **{k: record.get(k) for k in SUMMARY_FIELDS},
        "build_s": record["timing"]["build_s"],
        "deploy_s": record["timing"]["deploy_s"],
        "ready_after_deploy_s": record["timing"]["ready_after_deploy_s"],
        "tokens": record["tokens"]["total"]["total"],
        "agent_usd": record["cost"]["agent_usd"],
        "hosting_monthly_usd": record["cost"]["hosting_monthly_usd"],
        "shell_commands": sum(record["activity"]["shell_commands"].values()),
        "agent_version": record["agent"].get("version"),
        "build_tokens": record["tokens"]["build"].get("total"),
        "deploy_tokens": record["tokens"]["deploy"].get("total"),
        "stack": (record.get("code") or {}).get("frameworks") or [],
        "code_lines": (record.get("code") or {}).get("code_lines"),
        "dependencies": sum(((record.get("code") or {}).get("dependencies") or {}).values()),
        "deploy_config": (record.get("code") or {}).get("deploy_config") or [],
        "human_steps": [{"id": s["id"], "minutes": s["minutes"]} for s in (record.get("human") or {}).get("steps", [])],
        "security_score": (record.get("security") or {}).get("score"),
    }


def missing(cell: dict[str, Any]) -> dict[str, Any]:
    return {**{k: None for k in SUMMARY_FIELDS}, **cell, "status": "missing", "failure_stage": "harness",
            "score": 0.0, "checks_passed": 0, "checks_total": 0, "required_failed": [], "build_s": None,
            "deploy_s": None, "ready_after_deploy_s": None, "tokens": 0, "agent_usd": None,
            "hosting_monthly_usd": None, "shell_commands": 0, "agent_version": None, "build_tokens": None,
            "deploy_tokens": None, "stack": [], "code_lines": None, "dependencies": 0, "deploy_config": [],
            "human_steps": [], "security_score": None}


def mean(values: Iterable[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def total(values: Iterable[float | None]) -> tuple[float, bool]:
    """Sum of known values, plus whether any value was unknown."""
    values = list(values)
    return sum(v for v in values if v is not None), any(v is None for v in values)


def per_app_total(cells: list[dict[str, Any]], field: str) -> tuple[float, bool]:
    """Sum over apps of the mean over trials, so totals describe one pass over the apps."""
    sums, unknown = 0.0, False
    for app in sorted({c["app"] for c in cells}):
        values = [c[field] for c in cells if c["app"] == app and c["status"] != "missing"]
        known = [v for v in values if v is not None]
        unknown = unknown or len(known) < len([c for c in cells if c["app"] == app])
        sums += statistics.fmean(known) if known else 0.0
    return sums, unknown


def human_setup(cells: list[dict[str, Any]]) -> dict[str, float]:
    """Distinct human steps across cells: a person does each one once per cloud account."""
    steps = {s["id"]: s["minutes"] for c in cells for s in c.get("human_steps", [])}
    return {"count": len(steps), "minutes": sum(steps.values())}


def aggregate_group(cells: list[dict[str, Any]]) -> dict[str, Any]:
    finished = [c for c in cells if c["status"] != "missing"]
    tokens, _ = per_app_total(cells, "tokens")
    agent_usd, agent_unknown = per_app_total(cells, "agent_usd")
    hosting, hosting_unknown = per_app_total(cells, "hosting_monthly_usd")
    return {
        "cells": len(cells),
        "success": sum(c["status"] == "success" for c in cells),
        "partial": sum(c["status"] == "partial" for c in cells),
        "failed": sum(c["status"] in ("failed", "error", "missing") for c in cells),
        "blocked_on_human": sum(c.get("failure_stage") == "human" for c in cells),
        "human_steps": human_setup(finished),
        "security_score": mean(c.get("security_score") for c in finished),
        "success_rate": sum(c["status"] == "success" for c in cells) / len(cells) if cells else 0.0,
        "mean_score": mean(c["score"] for c in cells),
        "mean_build_s": mean(c["build_s"] for c in finished),
        "mean_deploy_s": mean(c["deploy_s"] for c in finished),
        "tokens": int(tokens),
        "agent_usd": round(agent_usd, 2),
        "agent_usd_incomplete": agent_unknown,
        "hosting_monthly_usd": round(hosting, 2),
        "hosting_incomplete": hosting_unknown,
    }


def summarize(run: dict[str, Any], cells: list[dict[str, Any]], cfg: config.Config) -> dict[str, Any]:
    groups = {}
    for model in cfg.models:
        for cloud in cfg.clouds:
            members = [c for c in cells if c["model"] == model.id and c["cloud"] == cloud.id]
            if members:
                groups[f"{model.id}/{cloud.id}"] = {"model": model.id, "cloud": cloud.id, **aggregate_group(members)}
    versions = sorted({c["agent_version"] for c in cells if c.get("agent_version")})
    return {"run": {**run, "agent_versions": versions}, "groups": list(groups.values()), "cells": cells}


# -- markdown ----------------------------------------------------------------------------------

def headline_table(summary: dict[str, Any], cfg: config.Config) -> list[str]:
    lines = []
    models = {g["model"] for g in summary["groups"]}
    for model in [m for m in cfg.models if m.id in models]:
        if len(models) > 1:
            lines += [f"**{model.name}**", ""]
        lines += [
            "| Cloud | Success | Human steps | Human time | Security | Checks passed | Avg build | Avg deploy | Tokens "
            "| Agent cost | Hosting / month |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for group in [g for g in summary["groups"] if g["model"] == model.id]:
            cloud = cfg.cloud(group["cloud"])
            people = group["human_steps"]
            lines.append(
                f"| [{cloud.name}]({cloud.url}) | {group['success']}/{group['cells']} | "
                f"{fmt.count(people['count'])} | {fmt.minutes(people['minutes'])} | {fmt.score(group['security_score'])} | "
                f"{fmt.pct(group['mean_score'])} | "
                f"{fmt.duration(group['mean_build_s'])} | {fmt.duration(group['mean_deploy_s'])} | "
                f"{fmt.tokens(group['tokens'])} | {fmt.usd(group['agent_usd'])}{'+' if group['agent_usd_incomplete'] else ''} | "
                f"{fmt.usd(group['hosting_monthly_usd'])}{'+' if group['hosting_incomplete'] else ''} |"
            )
        lines.append("")
    return lines


def app_matrix(summary: dict[str, Any], cfg: config.Config, link_prefix: str = "") -> list[str]:
    apps = [a for a in cfg.apps if any(c["app"] == a.id for c in summary["cells"])]
    lines = []
    models = {g["model"] for g in summary["groups"]}
    for model in [m for m in cfg.models if m.id in models]:
        if len(models) > 1:
            lines += [f"**{model.name}**", ""]
        lines += ["| Cloud | " + " | ".join(a.short or a.name for a in apps) + " |", "|---|" + "---|" * len(apps)]
        for cloud in cfg.clouds:
            row = []
            for app in apps:
                members = [c for c in summary["cells"] if c["model"] == model.id and c["cloud"] == cloud.id and c["app"] == app.id]
                row.append(matrix_cell(members, link_prefix))
            if any(r != fmt.DASH for r in row):
                lines.append(f"| {cloud.name} | " + " | ".join(row) + " |")
        lines.append("")
    return lines


def matrix_cell(members: list[dict[str, Any]], link_prefix: str) -> str:
    if not members:
        return fmt.DASH
    if len(members) > 1:
        wins = sum(c["status"] == "success" for c in members)
        return f"{wins}/{len(members)} ✅"
    c = members[0]
    label = fmt.status("human" if c.get("failure_stage") == "human" else c["status"])
    if c.get("failure_stage") == "human":
        label += " needs a person"
    elif c["status"] == "partial":
        label += f" {c['checks_passed']}/{c['checks_total']}"
    elif c["status"] in ("failed", "error", "missing"):
        label += f" {c['failure_stage']}"
    if link_prefix and c["status"] != "missing":
        return f"[{label}]({link_prefix}{cell_path(c)}.md)"
    return label


def run_title(run: dict[str, Any]) -> str:
    return f"{run['date']} · #{run['number']}" if run.get("number") else run["name"]


def run_order(summary: dict[str, Any]) -> tuple:
    run = summary["run"]
    return run.get("date", ""), int(run.get("number") or 0), int(run.get("attempt") or 0)


def render_summary(summary: dict[str, Any], cfg: config.Config) -> str:
    run = summary["run"]
    lines = [
        f"# Benchmark run {run['name']}",
        "",
        f"- Date: {run['date']}",
        f"- Agent: {cfg.agent.get('name', 'Claude Code')} {', '.join(run['agent_versions']) or cfg.agent.get('version', '')}",
        f"- Models: {', '.join(cfg.model(m).name for m in run['models'])}",
        f"- Scope: {run.get('scope', 'full')}",
        f"- Trials per cell: {run['trials']}",
    ]
    if run.get("url"):
        lines.append(f"- Workflow run: {run['url']}")
    lines += ["", "## Summary", ""] + headline_table(summary, cfg)
    lines += ["## By app", "", MATRIX_LEGEND, ""] + app_matrix(summary, cfg, link_prefix="")
    lines += [
        "## All cells",
        "",
        "| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security | Build | Deploy "
        "| Ready after | Tokens | Agent cost | Hosting / month |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in summary["cells"]:
        report = f"[{fmt.status(c['status'])} {c['status']}]({cell_path(c)}.md)" if c["status"] != "missing" else "❔ missing"
        people = human_setup([c]) if c["status"] != "missing" else None
        lines.append(
            f"| {c['model']} | {c['cloud']} | {c['app']} | {c['trial']} | {report} | {c['checks_passed']}/{c['checks_total']} | "
            f"{fmt.count(people['count']) if people else fmt.DASH} | {fmt.minutes(people['minutes']) if people else fmt.DASH} | "
            f"{fmt.score(c.get('security_score'))} | "
            f"{fmt.duration(c['build_s'])} | {fmt.duration(c['deploy_s'])} | {fmt.duration(c['ready_after_deploy_s'])} | "
            f"{fmt.tokens(c['tokens'])} | {fmt.usd(c['agent_usd'])} | {fmt.usd(c['hosting_monthly_usd'])} |"
        )
    lines += [
        "",
        "## What was built",
        "",
        "Every cell builds its app from scratch for its cloud, so stacks differ by platform.",
        "",
        "| Model | Cloud | App | Trial | Stack | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in summary["cells"]:
        if c["status"] == "missing":
            continue
        lines.append(
            f"| {c['model']} | {c['cloud']} | {c['app']} | {c['trial']} | {', '.join(c['stack']) or fmt.DASH} | "
            f"{fmt.tokens(c['code_lines'])} | {c['dependencies']} | {', '.join(c['deploy_config']) or fmt.DASH} | "
            f"{fmt.tokens(c['build_tokens'])} | {fmt.tokens(c['deploy_tokens'])} |"
        )
    lines += ["", LEGEND]
    return "\n".join(lines) + "\n"


MATRIX_LEGEND = ("✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · "
                 "🙋 blocked on something only a person can do · ❌ failed (stage shown) · "
                 "💥 the agent couldn't run (stage shown) · ❔ no result")

LEGEND = (
    "*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments "
    "to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. "
    "*Security* is an independent Claude Code review of how each app was deployed and what is live, scored "
    "against a fixed rubric. See the methodology. "
    "Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app "
    "took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost "
    "reported by Claude Code. Hosting is the estimated monthly cost of the resources left running, priced as "
    "always-on (730 h) with light traffic; usage-billed and free-tier resources can cost less in practice. `+` "
    "means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md)."
)


def render_index(runs: list[dict[str, Any]], cfg: config.Config) -> str:
    lines = [
        "# Results",
        "",
        "One folder per benchmark run under [`runs/`](runs), newest first. Each has a `summary.md`, a "
        "machine-readable `summary.json`, and per-cell `result.json` + report under `cells/`.",
        "",
        "Only full runs (every cloud, app and model) update the summary in the repository's README.",
        "",
    ]
    if not runs:
        return "\n".join(lines + ["No runs yet."]) + "\n"
    lines += [
        "| Run | Scope | Models | Success | Checks passed | Agent cost |",
        "|---|---|---|---|---|---|",
    ]
    for summary in runs:
        run, cells = summary["run"], summary["cells"]
        agent_usd, _ = total(c["agent_usd"] for c in cells)
        lines.append(
            f"| [{run_title(run)}](runs/{run['name']}/summary.md) | {run.get('scope', 'full')} | {', '.join(run['models'])} | "
            f"{sum(c['status'] == 'success' for c in cells)}/{len(cells)} | "
            f"{fmt.pct(mean(c['score'] for c in cells))} | {fmt.usd(agent_usd)} |"
        )
    return "\n".join(lines) + "\n"


def render_readme_section(summary: dict[str, Any], cfg: config.Config, runs_count: int) -> str:
    run = summary["run"]
    base = f"results/runs/{run['name']}/"
    lines = [
        f"Latest full run: [{run_title(run)}]({base}summary.md) · "
        f"{cfg.agent.get('name', 'Claude Code')} {', '.join(run['agent_versions']) or cfg.agent.get('version', '')} · "
        f"{', '.join(cfg.model(m).name for m in run['models'])}",
        "",
    ] + headline_table(summary, cfg) + app_matrix(summary, cfg, link_prefix=base) + [
        "Success counts deployments that passed every required check. *Human steps* and *human time* are what a "
        "person had to do, or would have to do, for the agent to deploy all the apps: distinct steps and estimated "
        "minutes. *Security* is the average score of an independent security review of each deployment. Times are "
        "averages per app; tokens, agent cost and hosting are totals across the apps (averaged over trials). Hosting "
        "is priced as always-on for a month. "
        f"[All {runs_count} run(s)](results/README.md) · [Methodology](docs/methodology.md)",
    ]
    return "\n".join(lines)


def update_readme(readme: Path, section: str) -> None:
    text = readme.read_text() if readme.exists() else ""
    block = f"{README_START}\n{section}\n{README_END}"
    if README_START in text and README_END in text:
        text = re.sub(re.escape(README_START) + r".*?" + re.escape(README_END), lambda _: block, text, flags=re.S)
    else:
        text = text.rstrip() + "\n\n## Latest results\n\n" + block + "\n"
    readme.write_text(text)


def scope(planned: list[dict[str, Any]], cfg: config.Config) -> str:
    """'full' when the run covers every model x cloud x app in benchmark.yaml, else what it covered."""
    covered = {(c["model"], c["cloud"], c["app"]) for c in planned}
    if covered >= {(m.id, c.id, a.id) for m in cfg.models for c in cfg.clouds for a in cfg.apps}:
        return "full"
    parts = []
    for label, key, items in (("apps", "app", cfg.apps), ("clouds", "cloud", cfg.clouds), ("models", "model", cfg.models)):
        chosen = [i.id for i in items if any(c[key] == i.id for c in planned)]
        parts.append(f"{label}: " + ("all" if len(chosen) == len(items) else ", ".join(chosen)))
    return " · ".join(parts)


# -- entry point -------------------------------------------------------------------------------

def aggregate(artifacts: Path, plan: dict[str, Any], results_dir: Path, readme: Path, run: dict[str, Any]) -> dict[str, Any]:
    cfg = config.load()
    run_dir = results_dir / "runs" / run["name"]
    found = load_results(artifacts)
    planned = sorted(plan["cells"], key=lambda c: (
        [m.id for m in cfg.models].index(c["model"]), [x.id for x in cfg.clouds].index(c["cloud"]),
        [a.id for a in cfg.apps].index(c["app"]), int(c["trial"])))
    cells = []
    for cell in planned:
        key = cell_key(cell)
        if key not in found:
            cells.append(missing(cell))
            continue
        record, source = found[key]
        target = run_dir / cell_path(cell)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
        report = source / "report.md"
        if report.exists():
            target.with_suffix(".md").write_text(report.read_text())
        cells.append(compact(record))
    run = {**run, "models": sorted({c["model"] for c in planned}, key=[m.id for m in cfg.models].index),
           "trials": max((int(c["trial"]) for c in planned), default=1), "scope": scope(planned, cfg)}
    summary = summarize(run, cells, cfg)
    # A run where no agent could work at all (say, a bad API key) says nothing about the clouds.
    summary["run"]["commit"] = any(c["status"] not in ("error", "missing") for c in cells)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run_dir / "summary.md").write_text(render_summary(summary, cfg))
    runs = []
    for path in (results_dir / "runs").glob("*/summary.json"):
        try:
            runs.append(json.loads(path.read_text()))
        except ValueError:
            continue
    runs.sort(key=run_order, reverse=True)
    (results_dir / "README.md").write_text(render_index(runs, cfg))
    # A partial run (a test of a few cells) must not replace the full comparison in the README.
    if run["scope"] == "full":
        update_readme(readme, render_readme_section(summary, cfg, len(runs)))
    return summary
