"""Merges a cell's step outputs into its result record (result.json) and renders report.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench import agent, fmt, human
from bench.clouds.base import parse_time

if TYPE_CHECKING:
    from bench.cell import Cell

SCHEMA_VERSION = 1
PHASE_SUMMARY_FIELDS = (
    "status", "detail", "started", "resumed", "started_at", "wall_time_s", "api_time_s", "turns", "tokens",
    "tokens_estimated", "cost_usd", "cost_source", "model_usage", "tool_calls", "tool_errors", "compactions",
    "api_retries", "result_subtype", "terminal_reason", "permission_denials", "model", "claude_code_version",
    "lingered",
)
MAX_COMMANDS_IN_REPORT = 80


def outcome(build: agent.Phase, deploy: agent.Phase, verification: dict[str, Any]) -> tuple[str, str | None]:
    """(status, failure stage): the first stage that didn't deliver a working app."""
    if verification.get("harness_error"):
        return "error", "harness"
    ran = [p for p in (build, deploy) if p.status != "not_run"]
    if ran and all(p.status in ("error", "crashed") and not p.tokens.get("total") for p in ran):
        return "error", "agent"  # the agent never worked: bad API key, model access, quota and so on
    if verification.get("success"):
        return "success", None
    if verification.get("url") and (verification.get("readiness") or {}).get("ready"):
        return "partial", "verify"
    if build.status != "completed" and deploy.status != "completed":
        return "failed", "build"
    return "failed", "deploy"


def add_tokens(*groups: dict[str, int]) -> dict[str, int]:
    keys = ("input", "output", "cache_read", "cache_write", "total")
    return {k: sum(int(g.get(k, 0)) for g in groups if g) for k in keys}


def ready_after_deploy(deploy: agent.Phase, verification: dict[str, Any], probe: dict[str, Any]) -> float | None:
    """Seconds from the agent finishing the deploy phase until the app answered with 2xx."""
    if probe.get("probed"):
        return probe.get("ready_after_deploy_s")
    # No URL in deployment.json, so only the verifier timed it, after the harness's own steps.
    deploy_start, verify_start = parse_time(deploy.started_at), parse_time(verification.get("started_at"))
    waited = (verification.get("readiness") or {}).get("seconds_to_ready")
    if not (deploy_start and verify_start and deploy.wall_time_s is not None and waited is not None):
        return None
    deploy_end = deploy_start.timestamp() + deploy.wall_time_s
    return round(max(0.0, verify_start.timestamp() + waited - deploy_end), 1)


def slim_resource(resource: dict[str, Any]) -> dict[str, Any]:
    details = {k: v for k, v in (resource.get("details") or {}).items() if k != "spec"}
    keep = ("kind", "id", "name", "plan", "url", "monthly_usd", "pricing", "matched_by", "created_at")
    return {**{k: resource.get(k) for k in keep}, "details": details}


def build(cell: "Cell") -> dict[str, Any]:
    info = cell.info
    built = cell.phase("build") or agent.Phase("build")
    deployed = cell.phase("deploy") or agent.Phase("deploy")
    inventory = cell.read("inventory.json") or {}
    verification = cell.read("verify.json") or {}
    teardown = cell.read("teardown.json") or {}
    deployment = cell.deployment()
    cloud_inventory = inventory.get("cloud") or {}
    status, stage = outcome(built, deployed, verification)
    people = human.assess(cell, inventory, deployment, succeeded=status == "success")
    if people["blocked"] and status != "success":
        stage = "human"  # it couldn't finish without something only a person can do

    costs = [c for c in (built.cost_usd, deployed.cost_usd) if c is not None]
    tool_calls: dict[str, int] = {}
    for phase in (built, deployed):
        for name, count in phase.tool_calls.items():
            tool_calls[name] = tool_calls.get(name, 0) + count
    cloud_teardown = teardown.get("cloud") or {}
    outcomes = cloud_teardown.get("outcomes", []) + (teardown.get("github") or {}).get("outcomes", [])

    cfg = cell.config
    return {
        "schema": SCHEMA_VERSION,
        "names": {"cloud": cfg.cloud(info["cloud"]).name, "model": cfg.model(info["model"]).name,
                  "app": cfg.app(info["app"]).name},
        "run_id": info["run_id"],
        "cloud": info["cloud"],
        "model": info["model"],
        "app": info["app"],
        "trial": info["trial"],
        "prefix": info["prefix"],
        "agent": {**info.get("agent", {}), "version": deployed.claude_code_version or built.claude_code_version
                  or info.get("agent", {}).get("version")},
        "status": status,
        "failure_stage": stage,
        "url": verification.get("url"),
        "url_source": verification.get("url_source"),
        "score": verification.get("score", 0.0),
        "checks_passed": verification.get("passed", 0),
        "checks_total": verification.get("passed", 0) + verification.get("failed", 0),
        "required_failed": verification.get("required_failed", []),
        "human": people,
        "timing": {
            "build_s": built.wall_time_s,
            "deploy_s": deployed.wall_time_s,
            "agent_s": round((built.wall_time_s or 0) + (deployed.wall_time_s or 0), 1),
            "ready_after_deploy_s": ready_after_deploy(deployed, verification, cell.read("deploy/ready.json") or {}),
            "verify_s": verification.get("duration_s"),
        },
        "tokens": {"build": built.tokens, "deploy": deployed.tokens, "total": add_tokens(built.tokens, deployed.tokens)},
        "cost": {
            "agent_usd": round(sum(costs), 6) if costs else None,
            "agent_build_usd": built.cost_usd,
            "agent_deploy_usd": deployed.cost_usd,
            "agent_cost_estimated": "estimated" in (built.cost_source, deployed.cost_source),
            "hosting_monthly_usd": cloud_inventory.get("monthly_usd"),
            "hosting_unpriced": cloud_inventory.get("unpriced", []),
            "hosting_agent_estimate_usd": deployment.get("estimated_monthly_cost_usd"),
        },
        "activity": {
            "turns": {"build": built.turns, "deploy": deployed.turns},
            "tool_calls": dict(sorted(tool_calls.items(), key=lambda kv: -kv[1])),
            "shell_commands": {"build": built.tool_calls.get("Bash", 0), "deploy": deployed.tool_calls.get("Bash", 0)},
            "tool_errors": built.tool_errors + deployed.tool_errors,
            "web_searches": tool_calls.get("WebSearch", 0),
            "web_fetches": tool_calls.get("WebFetch", 0),
            "subagents": tool_calls.get("Task", 0) + tool_calls.get("Agent", 0),
        },
        "phases": {
            "build": {k: getattr(built, k) for k in PHASE_SUMMARY_FIELDS},
            "deploy": {k: getattr(deployed, k) for k in PHASE_SUMMARY_FIELDS},
        },
        "final_messages": {"build": built.final_message[:3000], "deploy": deployed.final_message[:3000]},
        "deployment_manifest": deployment,
        "verification": {
            k: verification.get(k)
            for k in ("readiness", "performance", "checks", "browser", "error", "harness_error", "duration_s")
            if k in verification
        },
        "resources": [slim_resource(r) for r in cloud_inventory.get("resources", [])],
        "scratch_resources": [slim_resource(r) for r in (inventory.get("github") or {}).get("resources", [])],
        "possible_leaks": [slim_resource(r) for r in cloud_inventory.get("possible_leaks", [])],
        "account": cloud_inventory.get("account", {}),
        "inventory_errors": cloud_inventory.get("errors", []) + ([cloud_inventory["skipped"]] if cloud_inventory.get("skipped") else []),
        "teardown": {
            "skipped": teardown.get("skipped"),
            "kept": cloud_teardown.get("kept", []),
            "deleted": sum(1 for o in outcomes if o.get("deleted")),
            "failed": [o for o in outcomes if not o.get("deleted")],
            "leftovers": [r.get("name") for r in cloud_teardown.get("leftovers", [])],
        },
    }


def render_report(record: dict[str, Any], cell: "Cell | None" = None) -> str:
    t, tok, cost = record["timing"], record["tokens"], record["cost"]
    phases = record["phases"]
    names = record.get("names") or {}
    title = f"{names.get('app', record['app'])} on {names.get('cloud', record['cloud'])} with {names.get('model', record['model'])}"
    lines = [
        f"# {fmt.status(record['status'])} {title} (trial {record['trial']})",
        "",
        f"**{record['status']}**" + (f" (failed at {record['failure_stage']})" if record["failure_stage"] else "")
        + f": {record['checks_passed']}/{record['checks_total']} checks passed ({fmt.pct(record['score'])}).",
        "",
        f"- URL: {record['url'] or 'none'}" + (f" (from {record['url_source']})" if record.get("url_source") else ""),
        f"- Estimated hosting: {fmt.usd(cost['hosting_monthly_usd'])}/month"
        + (f" (the agent estimated {fmt.usd(_number(cost['hosting_agent_estimate_usd']))})"
           if cost.get("hosting_agent_estimate_usd") is not None else ""),
        f"- Agent: {record['agent'].get('name', 'Claude Code')} {record['agent'].get('version') or ''}, "
        f"model `{record['agent'].get('model')}`, effort {record['agent'].get('effort')}",
        f"- Resource prefix: `{record['prefix']}`",
        "",
        "| | Build | Deploy | Total |",
        "|---|---|---|---|",
        f"| Status | {phases['build']['status']} | {phases['deploy']['status']} | |",
        f"| Time | {fmt.duration(t['build_s'])} | {fmt.duration(t['deploy_s'])} | {fmt.duration(t['agent_s'])} |",
        f"| Turns | {phases['build']['turns'] or fmt.DASH} | {phases['deploy']['turns'] or fmt.DASH} | |",
        f"| Tokens | {fmt.tokens(tok['build'].get('total'))} | {fmt.tokens(tok['deploy'].get('total'))} | {fmt.tokens(tok['total']['total'])} |",
        f"| Agent cost | {fmt.usd(cost['agent_build_usd'])} | {fmt.usd(cost['agent_deploy_usd'])} | "
        f"{fmt.usd(cost['agent_usd'], cost['agent_cost_estimated'])} |",
        f"| Shell commands | {record['activity']['shell_commands']['build']} | {record['activity']['shell_commands']['deploy']} | |",
        "",
        f"App answered {fmt.duration(t['ready_after_deploy_s'])} after the agent finished deploying.",
        "",
        "## What was built",
        "",
        *architecture_lines(record.get("code") or {}),
        "",
        "## Human steps",
        "",
        *human_lines(record.get("human") or {}),
        "",
        "## Checks",
        "",
        "| Check | Required | Result | Detail |",
        "|---|---|---|---|",
    ]
    for check in (record["verification"].get("checks") or []):
        lines.append(f"| {fmt.cell(check['description'])} | {'yes' if check['required'] else 'no'} | "
                     f"{check['status']} | {fmt.cell(check['detail'][:240])} |")
    for key in ("error", "harness_error"):
        if record["verification"].get(key):
            lines.append(f"\nVerification error: {record['verification'][key]}")
    lines += ["", "## Cloud resources", ""]
    if record["resources"]:
        lines += ["| Kind | Name | Plan | $/month | How it was priced |", "|---|---|---|---|---|"]
        for r in record["resources"]:
            lines.append(f"| {r['kind']} | {fmt.cell(r['name'])} | {fmt.cell(r.get('plan') or fmt.DASH)} | "
                         f"{fmt.usd(r.get('monthly_usd'))} | {fmt.cell(r.get('pricing') or '')} |")
    else:
        lines.append("None found.")
    if record["possible_leaks"]:
        lines += ["", "Created during this cell without the prefix (not deleted automatically): "
                  + ", ".join(f"`{r['name']}` ({r['kind']})" for r in record["possible_leaks"])]
    td = record["teardown"]
    lines += ["", f"Teardown: {td['skipped'] or str(td['deleted']) + ' deleted'}"
              + (f", failed: {', '.join(f['name'] for f in td['failed'])}" if td["failed"] else "")
              + (f", left over: {', '.join(td['leftovers'])}" if td["leftovers"] else "")]
    if record["final_messages"].get("deploy"):
        lines += ["", "## Agent's deploy summary", "", _quote(record["final_messages"]["deploy"])]
    if cell is not None and (deployed := cell.phase("deploy")) and deployed.commands:
        lines += ["", "## Shell commands during deploy", ""]
        for command in deployed.commands[:MAX_COMMANDS_IN_REPORT]:
            first = command["command"].strip().splitlines()[0] if command["command"].strip() else ""
            lines.append(f"- `{fmt.duration(command['t'])}` {'❌ ' if command['error'] else ''}`{first[:200].replace('`', chr(39))}`")
        if len(deployed.commands) > MAX_COMMANDS_IN_REPORT:
            lines.append(f"- … {len(deployed.commands) - MAX_COMMANDS_IN_REPORT} more")
    return "\n".join(lines) + "\n"


def human_lines(people: dict[str, Any]) -> list[str]:
    """What a person had to do, or would have to do, for this deployment."""
    if not people.get("steps"):
        lines = ["None: the agent needed no human setup at all."]
    else:
        lines = [f"{people['count']} step(s), about {people['minutes']} min of a person's time"
                 + (". **Blocked:** the deploy couldn't finish without them." if people.get("blocked") else "."), ""]
        lines += [f"- **{s['description']}** (~{s['minutes']} min): {'; '.join(s['evidence'])[:400]}" for s in people["steps"]]
    unneeded = people.get("blockers", []) if people.get("succeeded") else []
    if unneeded:
        lines += ["", "Reported but not needed, since the deployment worked without them: "
                  + "; ".join(b["detail"][:120] for b in unneeded)]
    return lines


def architecture_lines(code: dict[str, Any]) -> list[str]:
    """The stack the agent chose for this cloud, from the workspace it left behind."""
    if code.get("error") or not code:
        return [f"No code statistics ({code.get('error') or 'workspace missing'})."]
    languages = ", ".join(f"{language} {count:,}" for language, count in code.get("lines", {}).items())
    deps = code.get("dependencies") or {}
    return [
        f"- Stack: {', '.join(f'`{f}`' for f in code.get('frameworks') or []) or fmt.DASH}",
        f"- Code: {code.get('code_lines', 0):,} lines in {code.get('files', 0)} files ({languages or 'none'})",
        f"- Dependencies: {deps.get('npm', 0)} npm, {deps.get('python', 0)} Python",
        f"- Deploy config: {', '.join(f'`{f}`' for f in code.get('deploy_config') or []) or 'none'}",
    ]


def render_step_summary(record: dict[str, Any]) -> str:
    t, cost = record["timing"], record["cost"]
    people = record.get("human") or {}
    return (
        f"### {fmt.status(record['status'])} {record['app']} on {record['cloud']} ({record['model']}): {record['status']}\n\n"
        "| Checks | Human steps | Build | Deploy | Tokens | Agent cost | Hosting/month |\n|---|---|---|---|---|---|---|\n"
        f"| {record['checks_passed']}/{record['checks_total']} | {fmt.human(people.get('count'), people.get('minutes'))} | "
        f"{fmt.duration(t['build_s'])} | {fmt.duration(t['deploy_s'])} | "
        f"{fmt.tokens(record['tokens']['total']['total'])} | {fmt.usd(cost['agent_usd'])} | {fmt.usd(cost['hosting_monthly_usd'])} |\n\n"
    )


def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">" for line in text.strip().splitlines())


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
