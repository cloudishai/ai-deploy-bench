"""End to end: every cell step with a fake `claude`, a real local app, then run aggregation."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

from bench import aggregate, cell, config, result
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
    assert "[Cloudish](https://cloudish.ai) | 0/5" in text


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
