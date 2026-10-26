"""End to end: every cell step with a fake `claude`, a real local app, then run aggregation."""

import json
import shutil
import sys
import textwrap
from pathlib import Path

import pytest

from bench import aggregate, cell, config, plan, result
from tests.reference_apps import Server, static_app

FIXTURES = Path(__file__).parent / "fixtures" / "stream"
SECRET = "sk-ant-test-0123456789abcdef"


@pytest.fixture
def fake_claude(tmp_path, monkeypatch):
    script = tmp_path / "fake-claude"
    script.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, os, sys
        sys.stdin.read()
        deploy = "--resume" in sys.argv
        if deploy:
            json.dump({{"url": os.environ["FAKE_DEPLOY_URL"], "resources": [], "estimated_monthly_cost_usd": 0}},
                      open("deployment.json", "w"))
        stream = {str(FIXTURES)!r} + ("/phase2.jsonl" if deploy else "/phase1.jsonl")
        for line in open(stream):
            print(line.rstrip(), flush=True)
        # An agent that echoes a secret: it must be redacted before anything is uploaded.
        print(json.dumps({{"type": "system", "subtype": "note", "leak": os.environ.get("ANTHROPIC_API_KEY", "")}}), flush=True)
        """))
    script.chmod(0o755)
    monkeypatch.setenv("BENCH_CLAUDE_BIN", str(script))
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    for name in ("CLOUDISH_API_KEY", "GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(name, raising=False)
    return script


def test_cell_pipeline_and_aggregation(fake_claude, tmp_path, monkeypatch):
    with Server(static_app()) as url:
        monkeypatch.setenv("FAKE_DEPLOY_URL", url)
        cell_dir = tmp_path / "cell"
        current = cell.prepare(cell_dir, tmp_path / "work", "123-1", "cloudish", "opus-5-5", "static", 1)
        assert current.workspace.name == current.prefix
        assert (current.workspace / "TASK.md").exists()

        build = cell.build(current)
        assert build.status == "completed" and build.started
        deploy = cell.deploy(current)
        assert deploy.resumed and deploy.status == "completed"
        assert "adb-" in (cell_dir / "prompts" / "deploy.md").read_text()

        inventory = cell.inventory(current)
        assert inventory["cloud"]["skipped"] == "credentials not available"
        verification = cell.verify(current, use_browser=False)
        assert verification["url"] == url and verification["url_source"] == "deployment.json"
        cell.teardown(current)
        record = cell.finalize(current)

    # Cloudish gets no provided credentials, so the first (no-credentials) attempt is the deploy, and
    # there is no separate fallback phase. It doesn't count as "deployed without a human" only because
    # a local server can't offer HTTPS, so the cell is partial rather than a success.
    assert record["no_human"]["used"] == "no_credentials" and record["no_human"]["attempted"]
    assert record["no_human"]["deploy_s"] is None and record["deploys_without_human"] is False
    # Everything passes except HTTPS, which a local server can't offer.
    assert record["status"] == "partial" and record["required_failed"] == ["https"]
    assert record["tokens"]["build"]["total"] == 61867
    assert record["tokens"]["deploy"]["total"] == 62328
    assert record["cost"]["agent_usd"] == pytest.approx(0.005202, abs=1e-6)
    assert record["timing"]["ready_after_deploy_s"] == 0.0  # answering as soon as the agent finished
    for path in cell_dir.rglob("*"):
        if path.is_file() and path.suffix in (".json", ".jsonl", ".md", ".log"):
            assert SECRET not in path.read_text(), f"secret leaked into {path}"
    assert "[REDACTED]" in (cell_dir / "build" / "transcript.jsonl").read_text()
    assert (cell_dir / "source.tar.gz").exists()
    assert "Shell commands during deploy" in (cell_dir / "report.md").read_text()
    assert "Deployed without credentials, but not working" in (cell_dir / "report.md").read_text()
    assert "Needed a human" not in (cell_dir / "report.md").read_text()
    assert "## What was built" in (cell_dir / "report.md").read_text()

    readme = tmp_path / "README.md"
    readme.write_text("# Bench\n\nIntro.\n\n<!-- results:start -->\nold\n<!-- results:end -->\n\nFooter.\n")
    plan = {"cells": [
        {"cloud": "cloudish", "model": "opus-5-5", "app": "static", "trial": 1},
        {"cloud": "cloudish", "model": "opus-5-5", "app": "crud", "trial": 1},
    ]}
    run = {"name": "2026-10-12_1-1", "date": "2026-10-12", "number": 1, "attempt": 1, "url": "https://example.com/run"}
    summary = aggregate.aggregate(tmp_path, plan, tmp_path / "results", readme, run)

    group = summary["groups"][0]
    assert (group["cells"], group["partial"], group["failed"]) == (2, 1, 1)
    run_dir = tmp_path / "results" / "runs" / "2026-10-12_1-1"
    assert json.loads((run_dir / "cells/opus-5-5/cloudish/static-t1.json").read_text())["status"] == "partial"
    assert (run_dir / "cells/opus-5-5/cloudish/static-t1.md").exists()
    assert "❔ missing" in (run_dir / "summary.md").read_text()
    assert "## What was built" in (run_dir / "summary.md").read_text()
    # A partial run is committed and indexed, but leaves the README's comparison alone.
    assert summary["run"]["scope"] == "apps: static, crud · clouds: cloudish · models: all"
    assert "old" in readme.read_text()
    index = (tmp_path / "results" / "README.md").read_text()
    assert "2026-10-12 · #1" in index and "apps: static, crud · clouds: cloudish" in index
    # The JSON files link to each other, so a tool can walk from the run index to every cell record.
    runs = json.loads((tmp_path / "results" / "index.json").read_text())
    assert runs["schema"] == summary["schema"] == result.SCHEMA_VERSION
    listed = runs["runs"][0]
    assert (listed["name"], listed["cells"], listed["success"]) == ("2026-10-12_1-1", 2, 0)
    assert listed["benchmark_version"] == summary["run"]["benchmark_version"] == config.load().version
    on_disk = json.loads((tmp_path / "results" / listed["summary"]).read_text())
    assert (run_dir / on_disk["cells"][0]["path"]).exists() and (run_dir / on_disk["cells"][0]["report"]).exists()
    assert on_disk["cells"][1]["status"] == "missing" and on_disk["cells"][1]["path"] is None

    cfg = config.load()
    full = {"cells": [{"cloud": c.id, "model": m.id, "app": a.id, "trial": 1}
                      for m in cfg.models for c in cfg.clouds for a in cfg.apps]}
    run = {**run, "name": "2026-10-12_2-1", "number": 2}
    assert aggregate.aggregate(tmp_path, full, tmp_path / "results", readme, run)["run"]["scope"] == "full"
    text = readme.read_text()
    assert text.startswith("# Bench\n\nIntro.") and text.rstrip().endswith("Footer.")
    assert "old" not in text and "Latest full run: [2026-10-12 · #2]" in text
    assert f"[Benchmark v{cfg.version}](CHANGES.md)" in text and "| Stack fit |" in text
    assert "Deploys without human" in text
    assert "[Cloudish](https://cloudish.ai) | 0/5" in text


def test_deploy_falls_back_to_keyed_when_the_no_credentials_attempt_fails(tmp_path, monkeypatch):
    """A cloud that needs a token: the no-credentials attempt can't deploy, so the harness provides
    the credentials and the same session reruns. That keyed attempt is the deploy result."""
    script = tmp_path / "fake-claude"
    # On a deploy attempt (resume), only write a working deployment.json when the cloud token is present.
    script.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, os, sys
        sys.stdin.read()
        if "--resume" in sys.argv and os.environ.get("RENDER_API_KEY"):
            json.dump({{"url": os.environ["FAKE_DEPLOY_URL"], "resources": [], "estimated_monthly_cost_usd": 0}},
                      open("deployment.json", "w"))
        stream = {str(FIXTURES)!r} + ("/phase2.jsonl" if "--resume" in sys.argv else "/phase1.jsonl")
        for line in open(stream):
            print(line.rstrip(), flush=True)
        """))
    script.chmod(0o755)
    monkeypatch.setenv("BENCH_CLAUDE_BIN", str(script))
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    monkeypatch.setenv("RENDER_API_KEY", "rnd_testtoken")
    for name in ("GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(name, raising=False)

    with Server(static_app()) as url:
        monkeypatch.setenv("FAKE_DEPLOY_URL", url)
        current = cell.prepare(tmp_path / "cell", tmp_path / "work", "9-1", "render", "opus-5-5", "static", 1)
        cell.build(current)
        deployed = cell.deploy(current)

    # The no-credentials attempt is kept as its own phase; the keyed attempt is the deploy result.
    assert current.phase("deploy_nohuman") is not None
    assert deployed.status == "completed"
    no_human = current.read("deploy/no_human.json")
    assert no_human["used"] == "credentials" and no_human["url_answered"] is False
    assert current.read("deployment.json")["url"] == url
    # The no-credentials attempt's prompt tells the agent no credentials are provided.
    assert "No credentials are provided for Render" in (current.dir / "prompts" / "deploy_nohuman.md").read_text()
    assert "RENDER_API_KEY" in (current.dir / "prompts" / "deploy.md").read_text()


def test_smoke_test_stub_runs_every_step(tmp_path, monkeypatch):
    monkeypatch.setenv("BENCH_CLAUDE_BIN", str(Path(cell.__file__).with_name("stub_agent.py")))
    for name in ("CLOUDISH_API_KEY", "GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(name, raising=False)
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "1-1", "cloudish", "opus-5-5", "crud", 1)
    assert cell.build(current).status == "completed"
    deploy = cell.deploy(current)
    assert deploy.resumed and deploy.cost_usd == 0
    cell.inventory(current)
    cell.verify(current, use_browser=False)
    cell.teardown(current)
    record = cell.finalize(current)
    assert (record["status"], record["failure_stage"]) == ("failed", "deploy")
    assert record["deployment_manifest"]["_error"] == "deployment.json was not written"
    assert record["tokens"]["total"]["total"] == 0


def test_group_totals_average_over_trials():
    cells = [
        {"app": "static", "status": "success", "tokens": 100, "agent_usd": 1.0, "hosting_monthly_usd": 0.0,
         "score": 1.0, "build_s": 10, "deploy_s": 20},
        {"app": "static", "status": "success", "tokens": 300, "agent_usd": 3.0, "hosting_monthly_usd": 0.0,
         "score": 1.0, "build_s": 30, "deploy_s": 40},
        {"app": "crud", "status": "failed", "tokens": 50, "agent_usd": 0.5, "hosting_monthly_usd": None,
         "score": 0.5, "build_s": 5, "deploy_s": 5},
    ]
    group = aggregate.aggregate_group(cells)
    assert group["tokens"] == 250 and group["agent_usd"] == 2.5  # mean per app, summed over apps
    assert group["hosting_monthly_usd"] == 0.0 and group["hosting_incomplete"]
    assert (group["success"], group["cells"]) == (2, 3)


def test_an_agent_that_cannot_reach_the_api_is_an_error_and_not_committed(tmp_path, monkeypatch):
    script = tmp_path / "claude-api-error"
    script.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, sys
        sys.stdin.read()
        error = "API Error: 400 The requested features are not available for HIPAA-configured organizations"
        print(json.dumps({{"type": "system", "subtype": "init", "session_id": "s", "model": "claude-opus-5-5"}}))
        print(json.dumps({{"type": "result", "subtype": "success", "is_error": True, "result": error, "num_turns": 1,
                          "total_cost_usd": 0, "usage": {{}}, "modelUsage": {{}}}}))
        """))
    script.chmod(0o755)
    monkeypatch.setenv("BENCH_CLAUDE_BIN", str(script))
    for name in ("CLOUDISH_API_KEY", "GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(name, raising=False)
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "1-1", "cloudish", "opus-5-5", "static", 1)
    build = cell.build(current)
    assert build.status == "error" and build.detail.startswith("API Error: 400")
    cell.deploy(current)
    cell.verify(current, use_browser=False)
    record = cell.finalize(current)
    assert (record["status"], record["failure_stage"]) == ("error", "agent")

    readme = tmp_path / "README.md"
    readme.write_text("# Bench\n")
    plan = {"cells": [{"cloud": "cloudish", "model": "opus-5-5", "app": "static", "trial": 1}]}
    run = {"name": "2026-10-13_9-1", "date": "2026-10-13", "number": 9, "attempt": 1, "url": ""}
    summary = aggregate.aggregate(tmp_path, plan, tmp_path / "results", readme, run)
    assert summary["run"]["commit"] is False
    assert "💥 agent" in (tmp_path / "results" / "runs" / "2026-10-13_9-1" / "summary.md").read_text()


def test_results_index_without_runs():
    assert aggregate.render_index([], config.load()).rstrip().endswith("No runs yet.")


def test_screenshots_reach_the_report_and_the_committed_results(tmp_path, monkeypatch):
    for name in ("CLOUDISH_API_KEY", "GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "1-1", "vercel", "opus-5-5", "static", 1)
    shots = current.dir / result.SCREENSHOTS
    shots.mkdir()
    for name, text in {"home": "Welcome to Northwind", "contact": f"Error: invalid key {SECRET}"}.items():
        (shots / f"{name}.jpg").write_bytes(b"\xff\xd8" + name.encode())
        (shots / f"{name}.txt").write_text(text)
    url = "https://adb-x-static.vercel.app"
    current.write("verify.json", {"url": url, "readiness": {"ready": True}, "checks": [], "screenshots": [
        {"name": "home", "caption": "The home page", "url": url + "/", "file": "home.jpg"},
        {"name": "contact", "caption": "The contact page", "url": url + "/contact", "file": "contact.jpg"},
        {"name": "docs", "caption": "The docs", "url": url + "/docs", "file": None, "error": "TimeoutError: slow"},
    ]})
    record = cell.finalize(current)
    # The contact page showed the API key, so its picture is gone, and only the home page is shown.
    assert [s.get("file") for s in record["screenshots"]] == ["screenshots/home.jpg", None, None]
    assert record["screenshots"][1]["error"] == "removed because the page showed a secret"
    assert not (shots / "contact.jpg").exists() and SECRET not in (shots / "contact.txt").read_text()
    report = (current.dir / "report.md").read_text()
    assert "![The home page](screenshots/home.jpg)" in report and "contact.jpg" not in report
    assert "- The docs: not captured (TimeoutError: slow)" in report

    readme = tmp_path / "README.md"
    readme.write_text("# Bench\n")
    plan = {"cells": [{"cloud": "vercel", "model": "opus-5-5", "app": "static", "trial": 1}]}
    run = {"name": "2026-10-13_10-1", "date": "2026-10-13", "number": 10, "attempt": 1, "url": ""}
    aggregate.aggregate(tmp_path / "cell", plan, tmp_path / "results", readme, run)
    run_dir = tmp_path / "results" / "runs" / run["name"]
    copied = run_dir / "cells" / "opus-5-5" / "vercel"
    assert (copied / "static-t1" / "home.jpg").read_bytes() == b"\xff\xd8home"
    assert "![The home page](static-t1/home.jpg)" in (copied / "static-t1.md").read_text()
    assert json.loads((copied / "static-t1.json").read_text())["screenshots"][0]["file"] == "static-t1/home.jpg"
    gallery = (run_dir / "summary.md").read_text().split("## Screenshots", 1)[1]
    assert '[<img src="cells/opus-5-5/vercel/static-t1/home.jpg" width="220" alt="Static site on Vercel">]' in gallery


BASE_RUN = "2026-10-14_13-1"


def rerun_railway(tmp_path, date="2026-10-15"):
    """Reruns Railway on top of committed run #13, its cells standing in for the new ones."""
    results = tmp_path / "results"
    shutil.copytree(Path(__file__).parent.parent / "results", results)
    source = results / "runs" / BASE_RUN / "cells" / "opus-5-5" / "railway"
    for app in config.load().apps:
        record = json.loads((source / f"{app.id}-t1.json").read_text())
        out = tmp_path / "artifacts" / app.id
        out.mkdir(parents=True)
        (out / "result.json").write_text(json.dumps({**record, "run_id": "999-1", "screenshots": []}))
        (out / "report.md").write_text(f"# Railway {app.id}, rerun\n")
    readme = tmp_path / "README.md"
    readme.write_text("# Bench\n\n<!-- results:start -->\nold\n<!-- results:end -->\n")
    run = {"name": f"{date}_14-1", "date": date, "number": 14, "attempt": 1, "url": "https://example.com/14"}
    cells = plan.plan(config.load(), clouds="railway")["cells"]
    return results, readme, run, {"cells": cells}


def test_a_rerun_of_one_cloud_completes_its_base_run(tmp_path):
    results, readme, run, rerun = rerun_railway(tmp_path)
    summary = aggregate.aggregate(tmp_path / "artifacts", rerun, results, readme, run, base_run=BASE_RUN)

    base = json.loads((results / "runs" / BASE_RUN / "summary.json").read_text())
    assert summary["run"]["scope"] == "full" and summary["run"]["rerun"] == "clouds: railway"
    assert summary["run"]["base_run"]["name"] == BASE_RUN and len(summary["cells"]) == len(base["cells"])
    for cell in summary["cells"]:
        assert (cell["from_run"] is None) == (cell["cloud"] == "railway")
        assert cell["cloud"] == "railway" or cell["from_run"]["url"] == base["run"]["url"]
    # The other clouds' results are the base run's, files included.
    groups = {g["cloud"]: g for g in summary["groups"]}
    for group in base["groups"]:
        if group["cloud"] != "railway":
            assert groups[group["cloud"]] == group
    run_dir = results / "runs" / run["name"]
    for cell in base["cells"]:
        if cell["cloud"] != "railway":
            assert (run_dir / cell["path"]).read_bytes() == (results / "runs" / BASE_RUN / cell["path"]).read_bytes()
            for shot in cell["screenshots"]:
                assert (run_dir / aggregate.cell_path(cell) / shot).is_file()
    assert "rerun" in (run_dir / "cells/opus-5-5/railway/static-t1.md").read_text()
    assert json.loads((run_dir / "cells/opus-5-5/railway/static-t1.json").read_text())["run_id"] == "999-1"

    # A merged run is full, so it updates the README, and says what it's made of everywhere.
    text = readme.read_text()
    assert "Latest full run: [2026-10-15 · #14]" in text and "old" not in text
    assert f"copied unchanged from [2026-10-14 · #13](results/runs/{BASE_RUN}/summary.md)" in text
    report = (run_dir / "summary.md").read_text()
    assert f"[2026-10-14 · #13](../{BASE_RUN}/summary.md)" in report and "(from 2026-10-14 · #13)" in report
    assert "full (clouds: railway rerun on 2026-10-14 · #13)" in (results / "README.md").read_text()
    listed = json.loads((results / "index.json").read_text())["runs"][0]
    assert listed["base_run"]["name"] == BASE_RUN and listed["scope"] == "full"

    # Trends skip the copied clouds, so the base run's results aren't plotted twice.
    from website import data
    runs = data.load(results)
    merged = next(r for r in runs if r.name == run["name"])
    assert merged.inherited("opus-5-5", "cloudish") and not merged.inherited("opus-5-5", "railway")
    success = next(m for m in data.metrics(config.load()) if m.id == "success")
    scoped, series = data.trend(runs, success, config.load())
    at = scoped.index(merged)
    values = {s.key: s.values[at] for s in series}
    assert values["opus-5-5/cloudish"] is None and values["opus-5-5/railway"] is not None
    assert merged.cell("opus-5-5", "cloudish", "static").workflow_url == base["run"]["url"]
    assert merged.cell("opus-5-5", "railway", "static").workflow_url == run["url"]


def test_a_rerun_refuses_a_base_run_it_cannot_stand_beside(tmp_path):
    results, readme, run, rerun = rerun_railway(tmp_path, date="2026-10-30")
    with pytest.raises(ValueError, match="16 days old"):
        aggregate.aggregate(tmp_path / "artifacts", rerun, results, readme, run, base_run=BASE_RUN)
    run = {**run, "date": "2026-10-15"}
    with pytest.raises(ValueError, match="isn't a full run.*benchmark v"):
        aggregate.aggregate(tmp_path / "artifacts", rerun, results, readme, run, base_run="2026-10-13_4-1")
    with pytest.raises(ValueError, match="no "):
        aggregate.aggregate(tmp_path / "artifacts", rerun, results, readme, run, base_run="2026-01-01_1-1")
    assert not (results / "runs" / run["name"]).exists() and "old" in readme.read_text()
