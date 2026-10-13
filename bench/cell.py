"""The lifecycle of one benchmark cell (cloud x model x app x trial).

    prepare -> build -> deploy -> inventory -> verify -> teardown -> finalize

Each step runs as its own GitHub Actions step and shares state through files in the cell
directory, so a step only receives the secrets it needs. In particular the build step never sees
cloud credentials, which keeps the agent from deploying before the deploy phase starts.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import time
import uuid
from pathlib import Path
from typing import Any

from bench import ROOT_PREFIX, agent, codestats, config, prompts, result
from bench.clouds import ADAPTERS, base
from bench.clouds.github import GitHub
from bench.redact import redact_tree, secret_values
from bench.verify import VERIFIERS
from bench.verify.browser import Browser

# Harness-only variables that must never reach the agent: tokens, and the runner's file commands,
# which would let the agent change the environment of later steps (the ones holding cloud tokens).
HARNESS_ONLY = ("GITHUB_TOKEN", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_OUTPUT", "GITHUB_STATE", "GITHUB_STEP_SUMMARY")
GITHUB_VARS = ("GH_TOKEN", "GH_OWNER")
MODEL_SECRETS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
# Hosts of dashboards, docs and APIs, never the deployed app (used when guessing a URL from text).
CONSOLE_HOSTS = {
    "github.com", "vercel.com", "api.vercel.com", "render.com", "dashboard.render.com", "api.render.com",
    "www.digitalocean.com", "cloud.digitalocean.com", "docs.digitalocean.com", "api.digitalocean.com",
    "cloudish.ai", "www.cloudish.ai", "do.cloudish.ai", "localhost", "127.0.0.1",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def make_prefix(run_id: str, cloud: str, model: str, app: str, trial: int) -> str:
    """A short, unique, provider-safe name prefix, e.g. adb-k3x9f-crud."""
    digest = int(hashlib.sha256(f"{run_id}/{cloud}/{model}/{app}/{trial}".encode()).hexdigest(), 16)
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    code = ""
    for _ in range(5):
        digest, index = divmod(digest, 36)
        code += alphabet[index]
    return f"{ROOT_PREFIX}-{code}-{app}"


def app_inputs(app_id: str) -> dict[str, Any]:
    """Per-cell values the deployed app must be configured with."""
    if app_id == "api":
        return {"api_keys": [f"bench-{secrets.token_hex(12)}" for _ in range(2)]}
    return {}


class Cell:
    def __init__(self, directory: Path) -> None:
        self.dir = directory
        self.info: dict[str, Any] = json.loads((directory / "cell.json").read_text())
        self.config = config.load()

    @property
    def workspace(self) -> Path:
        return Path(self.info["workspace"])

    @property
    def prefix(self) -> str:
        return self.info["prefix"]

    def read(self, name: str) -> dict[str, Any] | None:
        path = self.dir / name
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except ValueError:
            return None

    def write(self, name: str, data: Any) -> None:
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    def phase(self, name: str) -> agent.Phase | None:
        data = self.read(f"{name}/phase.json")
        return agent.Phase.from_dict(data) if data else None

    def deployment(self) -> dict[str, Any]:
        data = self.read("deployment.json") or {}
        return data if isinstance(data, dict) else {}


def agent_env(cfg: config.Config, cloud: config.Cloud | None, extra: dict[str, str] | None = None) -> dict[str, str]:
    """The agent's environment: no harness variables or tokens, and only `cloud`'s credentials."""
    hidden = set(HARNESS_ONLY) | cfg.credential_names() | set(GITHUB_VARS)
    env = {k: v for k, v in os.environ.items() if k not in hidden and not k.startswith(("BENCH_", "ACTIONS_"))}
    if cloud is not None:
        allowed = [c.env for c in cloud.provided_credentials]
        allowed += list(GITHUB_VARS) if all(os.environ.get(v) for v in GITHUB_VARS) else []
        env.update({name: os.environ[name] for name in allowed if os.environ.get(name)})
    env.update(extra or {})
    return env


def log(message: str) -> None:
    print(message, flush=True)


def claude_binary() -> str:
    return os.environ.get("BENCH_CLAUDE_BIN", "claude")


# -- steps -------------------------------------------------------------------------------------

def prepare(cell_dir: Path, workspace_root: Path, run_id: str, cloud_id: str, model_id: str, app_id: str, trial: int) -> Cell:
    cfg = config.load()
    cloud, model, app = cfg.cloud(cloud_id), cfg.model(model_id), cfg.app(app_id)
    prefix = make_prefix(run_id, cloud_id, model_id, app_id, trial)
    # Tools that name things after the folder (Vercel, Cloudish aliases) then get the prefix for free.
    workspace = workspace_root / prefix
    workspace.mkdir(parents=True, exist_ok=False)
    if app.fixtures:
        shutil.copytree(app.fixtures, workspace, dirs_exist_ok=True)
    (workspace / "TASK.md").write_text(app.task)
    cell_dir.mkdir(parents=True, exist_ok=True)
    info = {
        "run_id": run_id,
        "cloud": cloud.id,
        "model": model.id,
        "app": app.id,
        "trial": trial,
        "prefix": prefix,
        "workspace": str(workspace),
        "session_id": str(uuid.uuid4()),
        "inputs": app_inputs(app.id),
        "seeded_files": sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*") if p.is_file()),
        "agent": {**cfg.agent, "model": model.model, "effort": model.effort or "default"},
        "created_at": now(),
    }
    (cell_dir / "cell.json").write_text(json.dumps(info, indent=2))
    (cell_dir / "prompts").mkdir(exist_ok=True)
    (cell_dir / "prompts" / "build.md").write_text(prompts.build_prompt(cloud, app))
    log(f"prepared {cloud.name} / {model.name} / {app.name} (trial {trial}) as {prefix} in {workspace}")
    return Cell(cell_dir)


def build(cell: Cell) -> agent.Phase:
    cfg, model = cell.config, cell.config.model(cell.info["model"])
    phase = agent.run_phase(
        name="build",
        prompt=(cell.dir / "prompts" / "build.md").read_text(),
        cwd=cell.workspace,
        model=model.model,
        effort=model.effort,
        out_dir=cell.dir / "build",
        timeout_s=cfg.defaults["build_timeout_minutes"] * 60,
        session_id=cell.info["session_id"],
        max_budget_usd=cfg.defaults.get("max_budget_usd_per_phase"),
        env=agent_env(cfg, cloud=None),
        prices=cfg.model_prices,
        secrets=secrets_to_hide(cfg),
        claude=claude_binary(),
        log=log,
    )
    log(f"build {phase.status} in {phase.wall_time_s}s, {phase.tokens.get('total', 0):,} tokens, ${phase.cost_usd or 0:.2f}")
    return phase


def deploy(cell: Cell) -> agent.Phase:
    cfg = cell.config
    cloud, model, app = cfg.cloud(cell.info["cloud"]), cfg.model(cell.info["model"]), cfg.app(cell.info["app"])
    built = cell.phase("build")
    resume = bool(built and built.started)
    extra = {}
    if keys := cell.info["inputs"].get("api_keys"):
        extra["BENCH_API_KEYS"] = ",".join(keys)
    env = agent_env(cfg, cloud, extra=extra)
    prompt = prompts.deploy_prompt(cloud, app, cell.prefix, env, fresh_session=not resume)
    (cell.dir / "prompts" / "deploy.md").write_text(prompt)
    phase = agent.run_phase(
        name="deploy",
        prompt=prompt,
        cwd=cell.workspace,
        model=model.model,
        effort=model.effort,
        out_dir=cell.dir / "deploy",
        timeout_s=cfg.defaults["deploy_timeout_minutes"] * 60,
        session_id=cell.info["session_id"] if resume else str(uuid.uuid4()),
        resume=resume,
        previous=built.cumulative if built else None,
        max_budget_usd=cfg.defaults.get("max_budget_usd_per_phase"),
        env=env,
        prices=cfg.model_prices,
        secrets=secrets_to_hide(cfg),
        claude=claude_binary(),
        log=log,
    )
    manifest = read_manifest(cell.workspace / "deployment.json")
    cell.write("deployment.json", manifest)
    log(f"deploy {phase.status} in {phase.wall_time_s}s, {phase.tokens.get('total', 0):,} tokens, ${phase.cost_usd or 0:.2f}")
    if phase.status != "cancelled":
        cell.write("deploy/ready.json", probe_ready(cell, manifest, phase))
    return phase


def manifest_url(manifest: dict[str, Any]) -> str | None:
    url = manifest.get("url")
    if isinstance(url, str) and url.strip():
        url = url.strip()
        return url if "://" in url else "https://" + url
    return None


def probe_ready(cell: Cell, manifest: dict[str, Any], phase: agent.Phase) -> dict[str, Any]:
    """Times how long the app takes to answer once the agent is done, before any harness work."""
    url = manifest_url(manifest)
    if not url:
        return {"probed": False}
    probe = VERIFIERS[cell.info["app"]](url, ready_timeout=cell.config.defaults["ready_timeout_minutes"] * 60)
    try:
        readiness = probe.wait_ready()
    finally:
        probe.http.close()
    if readiness["ready"] and readiness["attempts"] == 1:
        after = 0.0  # already answering when the agent finished, as it was told to check
    elif readiness["ready"]:
        lingered = (phase.exit_time_s or 0) - (phase.wall_time_s or 0)
        after = round(lingered + readiness["seconds_to_ready"], 1)
    else:
        after = None
    log(f"readiness: {'answering' if readiness['ready'] else 'not answering'} at {url}"
        + (f", {after}s after the agent finished" if after else ""))
    return {"probed": True, "url": url, **readiness, "ready_after_deploy_s": after}


def read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_error": "deployment.json was not written"}
    try:
        data = json.loads(path.read_text())
    except ValueError as error:
        return {"_error": f"deployment.json is not valid JSON: {error}"}
    return data if isinstance(data, dict) else {"_error": "deployment.json is not a JSON object"}


def workspace_credentials(cell: Cell) -> list[dict[str, str]]:
    """Credentials for this cloud that the agent saved in .env files, other than the ones provided.

    Cloudish's docs, for one, tell agents to mint a key per project folder and keep it in .env;
    resources created with such a key are invisible to the provided one.
    """
    names = {c.env for c in cell.config.cloud(cell.info["cloud"]).credentials}
    found: dict[str, set[str]] = {}
    if cell.workspace.exists():
        for path in cell.workspace.rglob(".env*"):
            if not path.is_file() or any(part in codestats.EXCLUDED_DIRS for part in path.parts):
                continue
            for line in path.read_text(errors="ignore").splitlines():
                key, sep, value = line.partition("=")
                key, value = key.strip().removeprefix("export ").strip(), value.strip().strip("'\"")
                if sep and key in names and len(value) >= 8 and value != os.environ.get(key):
                    found.setdefault(key, set()).add(value)
    return [{name: value} for name, values in sorted(found.items()) for value in sorted(values)]


def adapters(cell: Cell) -> list[tuple[str, base.Cloud]]:
    """(role, adapter) pairs: the provided credentials, any the agent saved, and GitHub scratch."""
    cloud = ADAPTERS[cell.info["cloud"]]
    found = [("cloud", cloud(os.environ))]
    found += [("cloud", cloud({**os.environ, **overlay})) for overlay in workspace_credentials(cell)]
    github = GitHub(os.environ)
    if github.configured():
        found.append(("github", github))
    return found


def merge_inventories(reports: list[dict[str, Any]]) -> dict[str, Any]:
    # A credential that wasn't provided (Cloudish) only yields a "skipped" placeholder; any real
    # inventory, made with credentials the agent saved, replaces it.
    reports = [r for r in reports if not r.get("skipped")] or reports[:1]
    merged = dict(reports[0])
    for report in reports[1:]:
        for key in ("resources", "possible_leaks", "unpriced", "errors"):
            merged[key] = merged.get(key, []) + report.get(key, [])
        merged["monthly_usd"] = round((merged.get("monthly_usd") or 0) + (report.get("monthly_usd") or 0), 2)
    return merged


def inventory(cell: Cell) -> dict[str, Any]:
    deployment = cell.deployment()
    declared = [r for r in deployment.get("resources") or [] if isinstance(r, dict)]
    deployed = cell.phase("deploy")
    since = deployed.started_at if deployed else cell.info["created_at"]
    found: dict[str, list[dict[str, Any]]] = {}
    for role, adapter in adapters(cell):
        if not adapter.configured():
            found.setdefault(role, []).append({"skipped": "credentials not available", "resources": [], "monthly_usd": None})
            continue
        found.setdefault(role, []).append(base.inventory(adapter, cell.prefix, declared, since))
    report = {role: merge_inventories(reports) for role, reports in found.items()}
    cell.write("inventory.json", report)
    cloud = report["cloud"]
    log(f"inventory: {len(cloud.get('resources', []))} resource(s), est. ${cloud.get('monthly_usd') or 0:.2f}/month"
        + (f", {len(cloud['possible_leaks'])} possible leak(s)" if cloud.get("possible_leaks") else ""))
    return report


def resolve_url(cell: Cell) -> tuple[str | None, str]:
    if url := manifest_url(cell.deployment()):
        return url, "deployment.json"
    for resource in ((cell.read("inventory.json") or {}).get("cloud") or {}).get("resources", []):
        if resource.get("url"):
            return resource["url"], "provider inventory"
    deployed = cell.phase("deploy")
    for candidate in re.findall(r"https://[^\s)\]\"'`<>]+", deployed.final_message if deployed else ""):
        host = candidate.split("/")[2].split(":")[0].lower()
        if host not in CONSOLE_HOSTS and not host.endswith(("github.com", "githubusercontent.com")):
            return candidate.rstrip(".,"), "agent's final message"
    return None, ""


def verify(cell: Cell, use_browser: bool = True) -> dict[str, Any]:
    url, source = resolve_url(cell)
    started, started_at = time.monotonic(), now()
    if not url:
        report = {"url": None, "success": False, "readiness": {"ready": False}, "checks": [], "score": 0.0,
                  "passed": 0, "failed": 0, "skipped": 0, "required_failed": [], "error": "no deployment URL found"}
    else:
        browser = Browser.launch() if use_browser else None
        log(f"verifying {url} (from {source}){'' if browser else ' without a browser'}")
        if use_browser and not browser:
            log("::warning::Playwright failed to launch; browser checks will fail")
        # The deploy step already waited for the app; only a short grace period is needed here.
        probed = (cell.read("deploy/ready.json") or {}).get("probed")
        try:
            verifier = VERIFIERS[cell.info["app"]](
                url,
                inputs=cell.info["inputs"],
                deployment=cell.deployment(),
                browser=browser,
                browser_required=use_browser,
                ready_timeout=60 if probed else cell.config.defaults["ready_timeout_minutes"] * 60,
            )
            report = verifier.run_all()
        except Exception as error:
            report = {"success": False, "readiness": {}, "checks": [], "score": 0.0, "passed": 0, "failed": 0,
                      "skipped": 0, "required_failed": [], "harness_error": f"verifier crashed: {error!r}"}
        finally:
            if browser:
                browser.close()
        report.update(url=url, url_source=source, browser=bool(browser))
    report["started_at"] = started_at
    report["duration_s"] = round(time.monotonic() - started, 1)
    cell.write("verify.json", report)
    for check in report["checks"]:
        mark = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[check["status"]]
        log(f"  {mark} {check['id']}{': ' + check['detail'] if check['detail'] else ''}")
    log(f"verify: {report['passed']} passed, {report['failed']} failed, success={report['success']}")
    return report


def teardown(cell: Cell, keep: bool = False) -> dict[str, Any]:
    if keep:
        report: dict[str, Any] = {"skipped": "deployments kept (keep_deployments)"}
        cell.write("teardown.json", report)
        return report
    stop_agent_leftovers(cell)
    declared = [r for r in cell.deployment().get("resources") or [] if isinstance(r, dict)]
    deployed = cell.phase("deploy")
    since = deployed.started_at if deployed else cell.info["created_at"]
    report: dict[str, Any] = {}
    for role, adapter in adapters(cell):
        entry = report.setdefault(role, {"outcomes": [], "leftovers": [], "kept": [], "errors": []})
        if not adapter.configured():
            entry["skipped"] = "credentials not available"
            continue
        found = base.inventory(adapter, cell.prefix, declared, None)
        # Declared resources the agent merely reused (created before this cell) are never deleted.
        mine = [r for r in found["resources"] if r["matched_by"] == "prefix" or created_since(r, since)]
        kept = [r["name"] for r in found["resources"] if r not in mine]
        outcomes = base.teardown(adapter, mine)
        remaining = [r for r in base.inventory(type(adapter)(adapter.env), cell.prefix, declared, None)["resources"]
                     if r["name"] not in kept]
        entry["outcomes"] += outcomes
        entry["leftovers"] += remaining
        entry["kept"] += kept
        entry["errors"] += found["errors"]
        log(f"teardown {role}: deleted {sum(o['deleted'] for o in outcomes)}/{len(outcomes)}"
            + (f", {len(remaining)} left over" if remaining else ""))
    cell.write("teardown.json", report)
    return report


def stop_agent_leftovers(cell: Cell) -> None:
    """Kills what's left of a cancelled agent step so it can't create resources during teardown.

    Only on GitHub runners, which are single-use: elsewhere the process group id may be reused.
    """
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for phase in ("build", "deploy"):
        pid_file = cell.dir / phase / "agent.pid"
        if pid_file.exists():
            try:
                os.killpg(int(pid_file.read_text()), signal.SIGKILL)
                log(f"stopped leftover {phase} agent processes")
            except (ValueError, ProcessLookupError, PermissionError):
                pass


def created_since(resource: dict[str, Any], since: str) -> bool:
    created, start = base.parse_time(resource.get("created_at")), base.parse_time(since)
    return bool(created and start and created >= start)


def secrets_to_hide(cfg: config.Config, cell: Cell | None = None) -> list[str]:
    saved = [v for overlay in workspace_credentials(cell) for v in overlay.values()] if cell else []
    return secret_values(os.environ, cfg.credential_names() | set(MODEL_SECRETS) | {"GH_TOKEN"}, saved)


def redact(cell_dir: Path) -> int:
    """Masks secrets in every file of the cell directory; safe to run on a half-finished cell."""
    current = Cell(cell_dir) if (cell_dir / "cell.json").exists() else None
    return redact_tree(cell_dir, secrets_to_hide(config.load(), current))


def finalize(cell: Cell) -> dict[str, Any]:
    hidden = secrets_to_hide(cell.config, cell)
    ignore = set(cell.info.get("seeded_files", []))
    code: dict[str, Any] = {}
    if cell.workspace.exists():
        try:
            code = codestats.stats(cell.workspace, ignore)
            codestats.snapshot(cell.workspace, cell.dir / "source.tar.gz", ignore, hidden)
        except Exception as error:
            code["error"] = f"code statistics failed: {error!r}"
    record = result.build(cell)
    record["code"] = code
    cell.write("result.json", record)
    (cell.dir / "report.md").write_text(result.render_report(record, cell))
    redact_tree(cell.dir, hidden)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as f:
            f.write(result.render_step_summary(record))
    log(f"result: {record['status']} (score {record['score']:.0%}) -> {cell.dir / 'result.json'}")
    return record
