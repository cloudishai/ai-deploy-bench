"""Merges a cell's step outputs into its result record (result.json) and renders report.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench import agent, config, fmt, human
from bench.clouds.base import parse_time, rejected_credentials

if TYPE_CHECKING:
    from bench.cell import Cell

SCHEMA_VERSION = 9
SCREENSHOTS = "screenshots"  # the verifier's screenshots, under the cell directory
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
    # The no-human deploy attempt: present as a separate phase only when it didn't win and the keyed
    # attempt took over. When it won, it *is* the deploy phase above.
    nohuman = cell.phase("deploy_nohuman")
    no_human = cell.read("deploy/no_human.json") or {}
    inventory = cell.read("inventory.json") or {}
    verification = cell.read("verify.json") or {}
    teardown = cell.read("teardown.json") or {}
    deployment = cell.deployment()
    cloud_inventory = inventory.get("cloud") or {}
    status, stage = outcome(built, deployed, verification)
    # The benchmark's own credentials were refused (revoked, say), so the agent's blockers are the
    # harness's failure, not the cloud's.
    harness_failed = status != "success" and bool(cloud_inventory.get("credentials_rejected"))
    if harness_failed:
        status, stage = "error", "harness"
    people = human.assess(cell, inventory, deployment, succeeded=status == "success", harness_failed=harness_failed)
    if people["blocked"] and status != "success":
        stage = "human"  # it couldn't finish without something only a person can do
    # Deployed with no human help: the no-credentials attempt won and the app passed its checks.
    deploys_without_human = no_human.get("used") == "no_credentials" and status == "success"

    costs = [c for c in (built.cost_usd, deployed.cost_usd, nohuman.cost_usd if nohuman else None) if c is not None]
    tool_calls: dict[str, int] = {}
    for phase in (built, deployed):
        for name, count in phase.tool_calls.items():
            tool_calls[name] = tool_calls.get(name, 0) + count
    cloud_teardown = teardown.get("cloud") or {}
    outcomes = cloud_teardown.get("outcomes", []) + (teardown.get("github") or {}).get("outcomes", [])

    security = cell.read("security.json") or {"status": "not_run"}
    cfg = cell.config
    return {
        "schema": SCHEMA_VERSION,
        "benchmark_version": cfg.version,
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
        "deploys_without_human": deploys_without_human,
        "no_human": {
            "attempted": no_human.get("attempted", False),
            "used": no_human.get("used"),  # "no_credentials" (won) or "credentials" (fell back)
            "url_answered": no_human.get("url_answered", False),
            "deploy_s": nohuman.wall_time_s if nohuman else None,
            "tokens": (nohuman.tokens if nohuman else {}).get("total", 0),
            "agent_usd": nohuman.cost_usd if nohuman else None,
        },
        "url": verification.get("url"),
        "url_source": verification.get("url_source"),
        "score": verification.get("score", 0.0),
        "checks_passed": verification.get("passed", 0),
        "checks_total": verification.get("passed", 0) + verification.get("failed", 0),
        "required_failed": verification.get("required_failed", []),
        "human": people,
        "security": {k: v for k, v in security.items() if k != "stack_fit"},
        "stack_fit": security.get("stack_fit") or {"status": security.get("status", "not_run"), "detail": security.get("detail")},
        "timing": {
            "build_s": built.wall_time_s,
            "deploy_s": deployed.wall_time_s,
            "deploy_nohuman_s": nohuman.wall_time_s if nohuman else None,
            "agent_s": round((built.wall_time_s or 0) + (deployed.wall_time_s or 0)
                             + ((nohuman.wall_time_s or 0) if nohuman else 0), 1),
            "ready_after_deploy_s": ready_after_deploy(deployed, verification, cell.read("deploy/ready.json") or {}),
            "verify_s": verification.get("duration_s"),
        },
        "tokens": {"build": built.tokens, "deploy": deployed.tokens,
                   "deploy_nohuman": nohuman.tokens if nohuman else {},
                   "total": add_tokens(built.tokens, deployed.tokens, *([nohuman.tokens] if nohuman else []))},
        "cost": {
            "agent_usd": round(sum(costs), 6) if costs else None,
            "agent_build_usd": built.cost_usd,
            "agent_deploy_usd": deployed.cost_usd,
            "agent_nohuman_deploy_usd": nohuman.cost_usd if nohuman else None,
            "agent_cost_estimated": "estimated" in (built.cost_source, deployed.cost_source,
                                                    nohuman.cost_source if nohuman else None),
            "hosting_monthly_usd": cloud_inventory.get("monthly_usd"),
            # The deployment priced for a month at each traffic level in benchmark.yaml (hosting_usage).
            "hosting_usage": cloud_inventory.get("usage") or {},
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
        "screenshots": kept_screenshots(cell, verification),
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


def no_human_lines(record: dict[str, Any]) -> list[str]:
    """One line on the no-credentials deploy attempt that every cell now runs first."""
    nh = record.get("no_human") or {}
    if not nh.get("attempted"):
        return []
    if record.get("deploys_without_human"):
        return ["**Deployed without a human:** the agent deployed with no credentials provided — "
                "no human signup or token needed.", ""]
    if nh.get("used") == "no_credentials":
        return ["**Deployed without credentials, but not working:** the agent deployed with no credentials "
                "provided, but the app failed required checks, so it doesn't count as deployed without a human.", ""]
    extra = ""
    if nh.get("deploy_s") is not None:
        extra = (f" (that attempt took {fmt.duration(nh['deploy_s'])}, {fmt.tokens(nh.get('tokens'))} tokens, "
                 f"{fmt.usd(nh.get('agent_usd'))})")
    return ["**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the "
            f"cloud's credentials were provided and the agent redeployed{extra}.", ""]


def harness_lines(record: dict[str, Any]) -> list[str]:
    """Why a cell is a harness error when the cloud refused the benchmark's own credentials."""
    if record["failure_stage"] != "harness" or record["verification"].get("harness_error"):
        return []
    rejected = rejected_credentials(record.get("inventory_errors") or [])
    if not rejected:
        return []
    cloud = (record.get("names") or {}).get("cloud", record["cloud"])
    return [f"**Harness error:** {cloud} rejected the benchmark's own credentials (`{rejected}`), so this cell "
            f"says nothing about {cloud}. Update the secret and rerun it.", ""]


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
        "- Estimated hosting: " + (hosting_summary(cost.get("hosting_usage") or {}, cell)
                                    or f"{fmt.usd(cost['hosting_monthly_usd'])}/month")
        + (f" (the agent estimated {fmt.usd(_number(cost['hosting_agent_estimate_usd']))})"
           if cost.get("hosting_agent_estimate_usd") is not None else ""),
        f"- Agent: {record['agent'].get('name', 'Claude Code')} {record['agent'].get('version') or ''}, "
        f"model `{record['agent'].get('model')}`, effort {record['agent'].get('effort')}"
        + (", HIPAA organization" if record["agent"].get("hipaa") else ""),
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
        *no_human_lines(record),
        *harness_lines(record),
        *screenshot_lines(record.get("screenshots") or []),
        "## What was built",
        "",
        *technology_lines(record),
        *architecture_lines(record.get("code") or {}),
        "",
        "### Stack fit",
        "",
        *stack_fit_lines(record.get("stack_fit") or {}),
        "",
        "## Human steps",
        "",
        *human_lines(record.get("human") or {}),
        "",
        "## Security and compliance review",
        "",
        *security_lines(record.get("security") or {}),
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
    if usage := cost.get("hosting_usage"):
        labels = usage_labels(cell)
        lines += ["| Traffic | $/month | How it was priced |", "|---|---|---|"]
        lines += [f"| {labels.get(key, key)} | {fmt.usd(u['usd'])}{'+' if u['incomplete'] else ''} | {fmt.cell(u['basis'])} |"
                  for key, u in usage.items()]
        lines += ["", "Each resource's list price, at the size it was provisioned and always on:", ""]
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


def security_lines(review: dict[str, Any]) -> list[str]:
    if review.get("status") != "completed":
        return [f"Not scored: {review.get('detail') or review.get('status') or 'not run'}."]
    reviewer = review.get("reviewer") or {}
    lines = [
        f"**{review['score']:.0f}/100**, from an independent Claude Code review (`{reviewer.get('model')}`, "
        f"{reviewer.get('effort')} effort{', HIPAA organization' if reviewer.get('hipaa') else ''}, "
        f"{fmt.usd(reviewer.get('cost_usd'))}) of the process, the code, the hosting plan and the live app.",
        "",
        review.get("summary") or "",
        "",
        "| Criterion | Weight | Score | Rationale |",
        "|---|---|---|---|",
    ]
    lines += [f"| {fmt.cell(c['name'])} | {c['weight']} | {c['score']}/10 | {fmt.cell(c['rationale'])} |"
              for c in review.get("criteria", [])]
    if review.get("findings"):
        lines += ["", "Findings:", ""]
        lines += [f"- **{f['severity']}** · {' · '.join(filter(None, (f.get('source'), f['title'])))}: {f['evidence']}"
                  + (f" Fix: {f['recommendation']}" if f.get("recommendation") else "") for f in review["findings"]]
    return lines


def stack_fit_lines(fit: dict[str, Any]) -> list[str]:
    if fit.get("status") != "completed":
        return [f"Not rated: {fit.get('detail') or fit.get('status') or 'not run'}."]
    lines = [f"**{fit['score']:.0f}/100**, from the same independent review, judged against the app's requirements "
             "rather than a preferred stack.", "", fit.get("summary") or "", "",
             "| Criterion | Weight | Score | Rationale |", "|---|---|---|---|"]
    return lines + [f"| {fmt.cell(c['name'])} | {c['weight']} | {c['score']}/10 | {fmt.cell(c['rationale'])} |"
                    for c in fit.get("criteria", [])]


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


def kept_screenshots(cell: "Cell", verification: dict[str, Any]) -> list[dict[str, Any]]:
    """The verifier's screenshots, with `file` relative to the cell directory for those still on disk;
    redaction deletes any whose page showed a secret."""
    shots = []
    for shot in verification.get("screenshots") or []:
        entry = {k: shot.get(k) for k in ("name", "caption", "url")}
        if shot.get("file") and (cell.dir / SCREENSHOTS / shot["file"]).is_file():
            entry["file"] = f"{SCREENSHOTS}/{shot['file']}"
        else:
            entry["error"] = shot.get("error") or "removed because the page showed a secret"
        shots.append(entry)
    return shots


def screenshot_lines(shots: list[dict[str, Any]]) -> list[str]:
    """A report section showing each screenshot; images are linked relative to the report."""
    if not shots:
        return []
    lines = ["## Screenshots", ""]
    for shot in shots:
        if shot.get("file"):
            lines += [f"**{shot['caption']}** ({shot['url']})", "", f"![{shot['caption']}]({shot['file']})", ""]
        else:
            lines += [f"- {shot['caption']}: not captured ({shot.get('error')})", ""]
    return lines


def technology_lines(record: dict[str, Any]) -> list[str]:
    """The technologies the app used, by group (see bench/stack.py)."""
    return [f"- {group}: {', '.join(names)}" for group, names in (record.get("technologies") or {}).items()]


def architecture_lines(code: dict[str, Any]) -> list[str]:
    """The stack the agent chose for this cloud, from the workspace it left behind."""
    if code.get("error") or not code:
        return [f"No code statistics ({code.get('error') or 'workspace missing'})."]
    languages = ", ".join(f"{language} {count:,}" for language, count in code.get("lines", {}).items())
    deps = code.get("dependencies") or {}
    return [
        f"- Code: {code.get('code_lines', 0):,} lines in {code.get('files', 0)} files ({languages or 'none'})",
        f"- Dependencies: {deps.get('npm', 0)} npm, {deps.get('python', 0)} Python",
        f"- Deploy config: {', '.join(f'`{f}`' for f in code.get('deploy_config') or []) or 'none'}",
    ]


def render_step_summary(record: dict[str, Any]) -> str:
    t, cost = record["timing"], record["cost"]
    people = record.get("human") or {}
    return (
        f"### {fmt.status(record['status'])} {record['app']} on {record['cloud']} ({record['model']}): {record['status']}\n\n"
        "| Checks | Human steps | Human time | Security & compliance | Stack fit | Build | Deploy | Tokens | Agent cost | Hosting/month |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        f"| {record['checks_passed']}/{record['checks_total']} | {fmt.count(people.get('count'))} | "
        f"{fmt.minutes(people.get('minutes'))} | {fmt.score((record.get('security') or {}).get('score'))} | "
        f"{fmt.score((record.get('stack_fit') or {}).get('score'))} | "
        f"{fmt.duration(t['build_s'])} | {fmt.duration(t['deploy_s'])} | "
        f"{fmt.tokens(record['tokens']['total']['total'])} | {fmt.usd(cost['agent_usd'])} | "
        f"{hosting_summary(cost.get('hosting_usage') or {}) or fmt.usd(cost['hosting_monthly_usd'])} |\n\n"
    )


def usage_labels(cell: "Cell | None" = None) -> dict[str, str]:
    cfg = cell.config if cell is not None else config.load()
    return {u.id: u.label for u in cfg.hosting_usage}


def hosting_summary(usage: dict[str, Any], cell: "Cell | None" = None) -> str:
    """'Light use: $0.30/month, Busy: $21.66/month', from the record's hosting_usage."""
    labels = usage_labels(cell)
    return ", ".join(f"{labels.get(key, key)}: {fmt.usd(u['usd'])}{'+' if u['incomplete'] else ''}/month"
                     for key, u in usage.items())


def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">" for line in text.strip().splitlines())


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
