"""Collects cell results into results/runs/<run>/, rebuilds the run indexes and refreshes README.md.

The JSON files are meant for other tools to read: results/index.json lists the runs, each run's summary.json
lists its cells with the path of each cell's full record, and every file carries the result schema version.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import statistics
from pathlib import Path
from typing import Any, Iterable

from bench import config, fmt, stack
from bench.result import SCHEMA_VERSION

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


def copy_screenshots(record: dict[str, Any], source: Path, target: Path, report: str) -> tuple[dict[str, Any], str]:
    """Copies a cell's screenshots into a folder named like its report (`<app>-t<trial>/`) and points
    the record and the report at the copies."""
    shots = []
    for shot in record.get("screenshots") or []:
        file = shot.get("file")
        if file and (source / file).is_file():
            name = Path(file).name
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / file, target / name)
            report = report.replace(f"]({file})", f"]({target.name}/{name})")
            shot = {**shot, "file": f"{target.name}/{name}"}
        elif file:  # deleted by redaction after the report was written
            report = report.replace(f"![{shot.get('caption')}]({file})", "*Screenshot removed.*")
            shot = {**{k: v for k, v in shot.items() if k != "file"}, "error": "removed because the page showed a secret"}
        shots.append(shot)
    return {**record, "screenshots": shots}, report


def compact(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **{k: record.get(k) for k in SUMMARY_FIELDS},
        "path": f"{cell_path(record)}.json",
        "report": f"{cell_path(record)}.md",
        "build_s": record["timing"]["build_s"],
        "deploy_s": record["timing"]["deploy_s"],
        "ready_after_deploy_s": record["timing"]["ready_after_deploy_s"],
        "tokens": record["tokens"]["total"]["total"],
        "agent_usd": record["cost"]["agent_usd"],
        "hosting_monthly_usd": record["cost"]["hosting_monthly_usd"],
        "hosting_usage_usd": {k: u["usd"] for k, u in (record["cost"].get("hosting_usage") or {}).items()},
        "hosting_usage_incomplete": [k for k, u in (record["cost"].get("hosting_usage") or {}).items() if u["incomplete"]],
        "shell_commands": sum(record["activity"]["shell_commands"].values()),
        "agent_version": record["agent"].get("version"),
        "build_tokens": record["tokens"]["build"].get("total"),
        "deploy_tokens": record["tokens"]["deploy"].get("total"),
        "stack": (record.get("code") or {}).get("frameworks") or [],
        "technologies": stack.headline(record),
        "code_lines": (record.get("code") or {}).get("code_lines"),
        "dependencies": sum(((record.get("code") or {}).get("dependencies") or {}).values()),
        "deploy_config": (record.get("code") or {}).get("deploy_config") or [],
        "human_steps": [{"id": s["id"], "minutes": s["minutes"]} for s in (record.get("human") or {}).get("steps", [])],
        "deploys_without_human": record.get("deploys_without_human", False),
        "security_score": (record.get("security") or {}).get("score"),
        "stack_fit_score": (record.get("stack_fit") or {}).get("score"),
        "screenshots": [Path(shot["file"]).name for shot in record.get("screenshots") or [] if shot.get("file")],
        "from_run": None,
    }


def missing(cell: dict[str, Any]) -> dict[str, Any]:
    return {**{k: None for k in SUMMARY_FIELDS}, **cell, "status": "missing", "failure_stage": "harness",
            "score": 0.0, "checks_passed": 0, "checks_total": 0, "required_failed": [], "build_s": None,
            "deploy_s": None, "ready_after_deploy_s": None, "tokens": 0, "agent_usd": None,
            "hosting_monthly_usd": None, "hosting_usage_usd": {}, "hosting_usage_incomplete": [], "path": None,
            "report": None, "shell_commands": 0, "agent_version": None, "build_tokens": None, "deploy_tokens": None, "stack": [], "technologies": [], "code_lines": None, "dependencies": 0, "deploy_config": [],
            "human_steps": [], "deploys_without_human": False, "security_score": None, "stack_fit_score": None,
            "screenshots": [], "from_run": None}


def mean(values: Iterable[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def total(values: Iterable[float | None]) -> tuple[float, bool]:
    """Sum of known values, plus whether any value was unknown."""
    values = list(values)
    return sum(v for v in values if v is not None), any(v is None for v in values)


def per_app_total(cells: list[dict[str, Any]], field: str, usage: str | None = None) -> tuple[float, bool]:
    """Sum over apps of the mean over trials, so totals describe one pass over the apps. With `usage`,
    `field` is a dict of values per traffic level and that level's value is summed."""
    sums, unknown = 0.0, False
    for app in sorted({c["app"] for c in cells}):
        values = [(c.get(field) or {}).get(usage) if usage else c[field]
                  for c in cells if c["app"] == app and c["status"] != "missing"]
        known = [v for v in values if v is not None]
        unknown = unknown or len(known) < len([c for c in cells if c["app"] == app])
        sums += statistics.fmean(known) if known else 0.0
    return sums, unknown


def human_setup(cells: list[dict[str, Any]]) -> dict[str, float]:
    """Distinct human steps across cells: a person does each one once per cloud account."""
    steps = {s["id"]: s["minutes"] for c in cells for s in c.get("human_steps", [])}
    return {"count": len(steps), "minutes": sum(steps.values())}


def no_human_deploys(cells: list[dict[str, Any]]) -> dict[str, int]:
    """Apps the agent deployed with no credentials provided (any trial), out of the apps attempted."""
    apps = sorted({c["app"] for c in cells if c["status"] != "missing"})
    count = sum(any(c.get("deploys_without_human") for c in cells if c["app"] == app) for app in apps)
    return {"count": count, "total": len(apps)}


def aggregate_group(cells: list[dict[str, Any]]) -> dict[str, Any]:
    finished = [c for c in cells if c["status"] != "missing"]
    tokens, _ = per_app_total(cells, "tokens")
    agent_usd, agent_unknown = per_app_total(cells, "agent_usd")
    hosting, hosting_unknown = per_app_total(cells, "hosting_monthly_usd")
    usages = list(dict.fromkeys(k for c in cells for k in c.get("hosting_usage_usd") or {}))
    usage_totals = {k: per_app_total(cells, "hosting_usage_usd", usage=k) for k in usages}
    return {
        "cells": len(cells),
        "success": sum(c["status"] == "success" for c in cells),
        "partial": sum(c["status"] == "partial" for c in cells),
        "failed": sum(c["status"] in ("failed", "error", "missing") for c in cells),
        "blocked_on_human": sum(c.get("failure_stage") == "human" for c in cells),
        "human_steps": human_setup(finished),
        "deploys_without_human": no_human_deploys(cells),
        "security_score": mean(c.get("security_score") for c in finished),
        "stack_fit_score": mean(c.get("stack_fit_score") for c in finished),
        "success_rate": sum(c["status"] == "success" for c in cells) / len(cells) if cells else 0.0,
        "mean_score": mean(c["score"] for c in cells),
        "mean_build_s": mean(c["build_s"] for c in finished),
        "mean_deploy_s": mean(c["deploy_s"] for c in finished),
        "tokens": int(tokens),
        "agent_usd": round(agent_usd, 2),
        "agent_usd_incomplete": agent_unknown,
        "hosting_monthly_usd": round(hosting, 2),
        "hosting_incomplete": hosting_unknown,
        "hosting_usage_usd": {k: round(v, 2) for k, (v, _) in usage_totals.items()},
        "hosting_usage_incomplete": [k for k, (_, unknown) in usage_totals.items()
                                     if unknown or any(k in c.get("hosting_usage_incomplete", []) for c in finished)],
    }


def summarize(run: dict[str, Any], cells: list[dict[str, Any]], cfg: config.Config) -> dict[str, Any]:
    groups = {}
    for model in cfg.models:
        for cloud in cfg.clouds:
            members = [c for c in cells if c["model"] == model.id and c["cloud"] == cloud.id]
            if members:
                groups[f"{model.id}/{cloud.id}"] = {"model": model.id, "cloud": cloud.id, **aggregate_group(members)}
    versions = sorted({c["agent_version"] for c in cells if c.get("agent_version")})
    run = {**run, "benchmark_version": cfg.version, "agent_versions": versions}
    return {"schema": SCHEMA_VERSION, "run": run, "groups": list(groups.values()),
            "cells": cells}


# -- markdown ----------------------------------------------------------------------------------

def headline_table(summary: dict[str, Any], cfg: config.Config) -> list[str]:
    lines = []
    models = {g["model"] for g in summary["groups"]}
    for model in [m for m in cfg.models if m.id in models]:
        if len(models) > 1:
            lines += [f"**{model.name}**", ""]
        lines += [
            "| Cloud | Success | Deploys without human | Human steps | Human time | Security & compliance | Stack fit "
            "| Checks passed | Avg build | Avg deploy | Tokens | Agent cost | " + " | ".join(hosting_headers(cfg)) + " |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(cfg.hosting_usage),
        ]
        order = [x.id for x in cfg.clouds]
        # In benchmark.yaml's (alphabetical) order, whatever order the run recorded.
        for group in sorted([g for g in summary["groups"] if g["model"] == model.id], key=lambda g: order.index(g["cloud"])):
            cloud = cfg.cloud(group["cloud"])
            people = group["human_steps"]
            nohuman = group.get("deploys_without_human") or {"count": 0, "total": group["cells"]}
            lines.append(
                f"| [{cloud.name}]({cloud.url}) | {group['success']}/{group['cells']} | "
                f"{nohuman['count']}/{nohuman['total']} | "
                f"{fmt.count(people['count'])} | {fmt.minutes(people['minutes'])} | {fmt.score(group['security_score'])} | "
                f"{fmt.score(group.get('stack_fit_score'))} | {fmt.pct(group['mean_score'])} | "
                f"{fmt.duration(group['mean_build_s'])} | {fmt.duration(group['mean_deploy_s'])} | "
                f"{fmt.tokens(group['tokens'])} | {fmt.usd(group['agent_usd'])}{'+' if group['agent_usd_incomplete'] else ''} | "
                + " | ".join(hosting_values(group, cfg)) + " |"
            )
        lines.append("")
    return lines


def hosting_headers(cfg: config.Config) -> list[str]:
    return [f"Hosting, {u.label.lower()}" for u in cfg.hosting_usage]


def hosting_values(entry: dict[str, Any], cfg: config.Config) -> list[str]:
    """Monthly hosting per traffic level for a group or cell, `+` where some resources were unpriced."""
    costs, unknown = entry.get("hosting_usage_usd") or {}, entry.get("hosting_usage_incomplete") or []
    return [f"{fmt.usd(costs.get(u.id))}{'+' if u.id in unknown else ''}" for u in cfg.hosting_usage]


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


def merged_note(run: dict[str, Any], link_prefix: str) -> str:
    """'Reran clouds: railway; the other cells are from [2026-10-14 · #13](...)', for merged runs."""
    base = run.get("base_run")
    if not base:
        return ""
    return (f"Reran {run.get('rerun', 'some cells')}; the other cells are copied unchanged from "
            f"[{run_title(base)}]({link_prefix}{base['name']}/summary.md)")


def run_scope(run: dict[str, Any]) -> str:
    """The run's scope, and for a merged run what was rerun and on top of which run."""
    if base := run.get("base_run"):
        return f"{run.get('scope', 'full')} ({run.get('rerun')} rerun on {run_title(base)})"
    return run.get("scope", "full")


def run_order(summary: dict[str, Any]) -> tuple:
    run = summary["run"]
    return run.get("date", ""), int(run.get("number") or 0), int(run.get("attempt") or 0)


def render_summary(summary: dict[str, Any], cfg: config.Config) -> str:
    run = summary["run"]
    lines = [
        f"# Benchmark run {run['name']}",
        "",
        f"- Date: {run['date']}",
        f"- Benchmark version: {run.get('benchmark_version', 1)} ([changes](../../../CHANGES.md))",
        f"- Agent: {cfg.agent.get('name', 'Claude Code')} {', '.join(run['agent_versions']) or cfg.agent.get('version', '')}",
        f"- Models: {', '.join(cfg.model(m).label for m in run['models'])}",
        f"- Scope: {run.get('scope', 'full')}",
        f"- Trials per cell: {run['trials']}",
    ]
    if run.get("url"):
        lines.append(f"- Workflow run: {run['url']}")
    if note := merged_note(run, "../"):
        lines.append(f"- {note}")
    lines += ["", "## Summary", ""] + headline_table(summary, cfg)
    lines += ["## By app", "", MATRIX_LEGEND, ""] + app_matrix(summary, cfg, link_prefix="")
    lines += [
        "## All cells",
        "",
        "| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Stack fit "
        "| Build | Deploy | Ready after | Tokens | Agent cost | " + " | ".join(hosting_headers(cfg)) + " |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(cfg.hosting_usage),
    ]
    for c in summary["cells"]:
        report = f"[{fmt.status(c['status'])} {c['status']}]({cell_path(c)}.md)" if c["status"] != "missing" else "❔ missing"
        if c.get("from_run"):
            report += f" (from {run_title(c['from_run'])})"
        people = human_setup([c]) if c["status"] != "missing" else None
        lines.append(
            f"| {c['model']} | {c['cloud']} | {c['app']} | {c['trial']} | {report} | {c['checks_passed']}/{c['checks_total']} | "
            f"{fmt.count(people['count']) if people else fmt.DASH} | {fmt.minutes(people['minutes']) if people else fmt.DASH} | "
            f"{fmt.score(c.get('security_score'))} | {fmt.score(c.get('stack_fit_score'))} | "
            f"{fmt.duration(c['build_s'])} | {fmt.duration(c['deploy_s'])} | {fmt.duration(c['ready_after_deploy_s'])} | "
            f"{fmt.tokens(c['tokens'])} | {fmt.usd(c['agent_usd'])} | " + " | ".join(hosting_values(c, cfg)) + " |"
        )
    lines += [
        "",
        "## What was built",
        "",
        "Every cell builds its app from scratch for its cloud, so stacks differ by platform.",
        "",
        "| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in summary["cells"]:
        if c["status"] == "missing":
            continue
        lines.append(
            f"| {c['model']} | {c['cloud']} | {c['app']} | {c['trial']} | {', '.join(c.get('technologies') or c['stack']) or fmt.DASH} | "
            f"{fmt.tokens(c['code_lines'])} | {c['dependencies']} | {', '.join(c['deploy_config']) or fmt.DASH} | "
            f"{fmt.tokens(c['build_tokens'])} | {fmt.tokens(c['deploy_tokens'])} |"
        )
    lines += ["", LEGEND, ""] + screenshot_gallery(summary, cfg)
    return "\n".join(lines).rstrip("\n") + "\n"


def screenshot_gallery(summary: dict[str, Any], cfg: config.Config) -> list[str]:
    """The first screenshot of each app on each cloud (first trial), each linked to its cell report."""
    cells = [c for c in summary["cells"] if c.get("screenshots") and int(c["trial"]) == 1]
    if not cells:
        return []
    lines = ["## Screenshots", "", "What the verifier saw on each deployment. Each picture links to its cell's report, "
             "which has the rest.", ""]
    for model in [m for m in cfg.models if any(c["model"] == m.id for c in cells)]:
        mine = {(c["cloud"], c["app"]): c for c in cells if c["model"] == model.id}
        clouds = [x for x in cfg.clouds if any(cloud == x.id for cloud, _ in mine)]
        if len(summary["run"]["models"]) > 1:
            lines += [f"**{model.name}**", ""]
        lines += ["| App | " + " | ".join(x.name for x in clouds) + " |", "|---|" + "---|" * len(clouds)]
        for app in [a for a in cfg.apps if any(name == a.id for _, name in mine)]:
            row = []
            for cloud in clouds:
                cell = mine.get((cloud.id, app.id))
                row.append(f'[<img src="{cell_path(cell)}/{cell["screenshots"][0]}" width="220" '
                           f'alt="{app.short or app.name} on {cloud.name}">]({cell_path(cell)}.md)' if cell else fmt.DASH)
            lines.append(f"| {app.short or app.name} | " + " | ".join(row) + " |")
        lines.append("")
    return lines


MATRIX_LEGEND = ("✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · "
                 "🙋 blocked on something only a person can do · ❌ failed (stage shown) · "
                 "💥 the agent couldn't run (stage shown) · ❔ no result")

LEGEND = (
    "*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments "
    "to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. "
    "*Security & compliance* is an independent Claude Code review of how each app was deployed, whether its "
    "hosting plan fits how the app is used, and what is live, scored against a fixed rubric. *Stack fit* is the same "
    "review's rating of the stack the agent chose, judged against the app's requirements. See the methodology. "
    "Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app "
    "took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost "
    "reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of "
    "traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit "
    "around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, "
    "are priced on the cheapest plan that allows it. `+` means some values were unknown. "
    "See [docs/methodology.md](../../../docs/methodology.md#hosting-cost)."
)


def render_index(runs: list[dict[str, Any]], cfg: config.Config) -> str:
    lines = [
        "# Results",
        "",
        "One folder per benchmark run under [`runs/`](runs), newest first. Each has a `summary.md`, a "
        "machine-readable `summary.json`, and a record (`<app>-t<trial>.json`) and report (`.md`) per cell under "
        "`cells/<model>/<cloud>/`. [`index.json`](index.json) lists every run for tools that read the results.",
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
            f"| [{run_title(run)}](runs/{run['name']}/summary.md) | {run_scope(run)} | {', '.join(run['models'])} | "
            f"{sum(c['status'] == 'success' for c in cells)}/{len(cells)} | "
            f"{fmt.pct(mean(c['score'] for c in cells))} | {fmt.usd(agent_usd)} |"
        )
    return "\n".join(lines) + "\n"


def render_json_index(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Every run, newest first, with the paths of its summaries, relative to results/."""
    entries = []
    for summary in runs:
        run, cells = summary["run"], summary["cells"]
        entries.append({
            **{k: run.get(k) for k in ("name", "date", "number", "attempt", "url", "scope", "models", "trials",
                                       "benchmark_version", "agent_versions", "base_run", "rerun")},
            "schema": summary.get("schema", 1),
            "cells": len(cells),
            "success": sum(c["status"] == "success" for c in cells),
            "summary": f"runs/{run['name']}/summary.json",
            "report": f"runs/{run['name']}/summary.md",
        })
    return {"schema": SCHEMA_VERSION, "runs": entries}


def render_readme_section(summary: dict[str, Any], cfg: config.Config, runs_count: int) -> str:
    run = summary["run"]
    base = f"results/runs/{run['name']}/"
    lines = [
        f"Latest full run: [{run_title(run)}]({base}summary.md) · "
        f"[Benchmark v{run.get('benchmark_version', 1)}](CHANGES.md) · "
        f"{cfg.agent.get('name', 'Claude Code')} {', '.join(run['agent_versions']) or cfg.agent.get('version', '')} · "
        f"{', '.join(cfg.model(m).label for m in run['models'])}",
        "",
    ] + ([merged_note(run, "results/runs/") + ".", ""] if run.get("base_run") else []) + headline_table(summary, cfg) + app_matrix(summary, cfg, link_prefix=base) + [
        "Success counts deployments that passed every required check. *Human steps* and *human time* are what a "
        "person had to do, or would have to do, for the agent to deploy all the apps: distinct steps and estimated "
        "minutes. *Security & compliance* is the average score of an independent review of each deployment's security "
        "and of whether its hosting plan fits the app's use, and *stack fit* the same review's rating of the stack the "
        "agent chose for each app, against the app's requirements. Times are "
        "averages per app; tokens, agent cost and hosting are totals across the apps (averaged over trials). Hosting "
        "is a month's cost with *light use* (a few visits a week) and when *busy* (hit around the clock). "
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


# -- reruns ------------------------------------------------------------------------------------

# How old a base run may be. Cells in a merged run should come from roughly the same time, since
# clouds change their products, prices and limits.
MAX_BASE_AGE_DAYS = 7


def load_base(results_dir: Path, name: str, run: dict[str, Any], cfg: config.Config) -> dict[str, Any]:
    """The summary of the run a rerun completes, after checking its cells can stand beside new ones."""
    path = results_dir / "runs" / name / "summary.json"
    if not path.is_file():
        raise ValueError(f"base run {name}: no {path}")
    base = json.loads(path.read_text())
    info = base["run"]
    problems = []
    if info.get("scope", "full") != "full":
        problems.append(f"it isn't a full run (scope: {info.get('scope')})")
    if info.get("benchmark_version") != cfg.version:
        problems.append(f"it ran benchmark v{info.get('benchmark_version')}, not v{cfg.version}")
    if info.get("agent_versions") and info["agent_versions"] != [cfg.agent.get("version")]:
        problems.append(f"it ran Claude Code {', '.join(info['agent_versions'])}, not {cfg.agent.get('version')}")
    if set(info.get("models") or []) != {m.id for m in cfg.models}:
        problems.append(f"it ran models {', '.join(info.get('models') or [])}")
    age = (dt.date.fromisoformat(run["date"]) - dt.date.fromisoformat(info["date"])).days
    if age > MAX_BASE_AGE_DAYS:
        problems.append(f"it is {age} days old (at most {MAX_BASE_AGE_DAYS})")
    if problems:
        raise ValueError(f"base run {name} can't be merged: " + "; ".join(problems))
    return base


def inherit(base: dict[str, Any], results_dir: Path, run_dir: Path) -> list[dict[str, Any]]:
    """Copies the base run's cells (records, reports and screenshots) into this run, unchanged, and
    returns their summary rows marked with the run that produced them."""
    source_dir = results_dir / "runs" / base["run"]["name"]
    origin = {k: base["run"].get(k) for k in ("name", "date", "number", "attempt", "url")}
    rows = []
    for row in base["cells"]:
        if row["status"] != "missing":
            target = run_dir / cell_path(row)
            target.parent.mkdir(parents=True, exist_ok=True)
            for suffix in (".json", ".md"):
                if (source_dir / cell_path(row)).with_suffix(suffix).is_file():
                    shutil.copyfile((source_dir / cell_path(row)).with_suffix(suffix), target.with_suffix(suffix))
            if (source_dir / cell_path(row)).is_dir():
                shutil.copytree(source_dir / cell_path(row), target, dirs_exist_ok=True)
        # A cell already inherited by the base run keeps pointing at the run that produced it.
        rows.append({**row, "from_run": row.get("from_run") or origin})
    return rows


# -- entry point -------------------------------------------------------------------------------

def aggregate(artifacts: Path, plan: dict[str, Any], results_dir: Path, readme: Path, run: dict[str, Any],
              base_run: str | None = None) -> dict[str, Any]:
    """With `base_run`, the planned cells replace that run's cells and the rest are copied from it, so
    rerunning part of a full run (say, one cloud after a fix to its adapter) yields a full run again."""
    cfg = config.load()
    run_dir = results_dir / "runs" / run["name"]
    found = load_results(artifacts)
    order = lambda c: ([m.id for m in cfg.models].index(c["model"]), [x.id for x in cfg.clouds].index(c["cloud"]),
                       [a.id for a in cfg.apps].index(c["app"]), int(c["trial"]))
    planned = sorted(plan["cells"], key=order)
    inherited = []
    if base_run:
        base = load_base(results_dir, base_run, run, cfg)
        rerun = {cell_key(c) for c in planned}
        base = {**base, "cells": [c for c in base["cells"] if cell_key(c) not in rerun]}
        inherited = inherit(base, results_dir, run_dir)
        run = {**run, "base_run": {k: base["run"].get(k) for k in ("name", "date", "number", "attempt", "url")},
               # What was rerun, without the dimensions it covered in full ("clouds: railway").
               "rerun": " · ".join(p for p in scope(planned, cfg).split(" · ") if not p.endswith(": all"))}
    cells = []
    for cell in planned:
        key = cell_key(cell)
        if key not in found:
            cells.append(missing(cell))
            continue
        record, source = found[key]
        target = run_dir / cell_path(cell)
        target.parent.mkdir(parents=True, exist_ok=True)
        report = source / "report.md"
        record, report_text = copy_screenshots(record, source, target, report.read_text() if report.exists() else "")
        target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
        if report.exists():
            target.with_suffix(".md").write_text(report_text)
        cells.append(compact(record))
    # Only the cells this run produced decide whether it's worth committing.
    fresh = cells
    cells = sorted(cells + inherited, key=order)
    run = {**run, "models": sorted({c["model"] for c in cells}, key=[m.id for m in cfg.models].index),
           "trials": max((int(c["trial"]) for c in cells), default=1), "scope": scope(cells, cfg)}
    summary = summarize(run, cells, cfg)
    # A run where no agent could work at all (say, a bad API key) says nothing about the clouds.
    summary["run"]["commit"] = any(c["status"] not in ("error", "missing") for c in fresh)
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
    (results_dir / "index.json").write_text(json.dumps(render_json_index(runs), indent=2) + "\n")
    # A partial run (a test of a few cells) must not replace the full comparison in the README.
    if run["scope"] == "full":
        update_readme(readme, render_readme_section(summary, cfg, len(runs)))
    return summary
