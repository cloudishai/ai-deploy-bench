import json
import sys
import textwrap

import pytest

from bench import cell, config, result, security

SECRET = "sk-ant-test-security-0123456789"


def review(**scores):
    return {"criteria": {k: {"score": v, "rationale": f"{k} rationale"} for k, v in scores.items()},
            "findings": [{"severity": "low", "criterion": "transport", "title": "No HSTS", "evidence": "curl -I"},
                         {"severity": "critical", "criterion": "secrets", "title": "Token in logs", "evidence": "deploy.md"}],
            "summary": "Mostly fine."}


ALL_TENS = dict(secrets=10, provenance=10, compliance=10, least_privilege=10, transport=10, exposure=10, application=10)


def test_score_weights_the_rubric():
    rubric = config.load().security_rubric
    assert security.score(rubric, review(**ALL_TENS))[0] == 100
    mixed = {**ALL_TENS, "secrets": 0, "provenance": 5}  # weights 25 and 20
    assert security.score(rubric, review(**mixed))[0] == pytest.approx(100 - 25 - 10)


def test_incomplete_reviews_are_rejected():
    rubric = config.load().security_rubric
    value, _, problems = security.score(rubric, review(secrets=10, transport=11))
    assert value is None and "missing or invalid score for provenance" in problems
    assert "missing or invalid score for transport" in problems  # out of range
    assert security.score(rubric, {"summary": "no criteria"})[2] == ["no criteria object"]


def test_findings_are_sorted_by_severity():
    assert [f["severity"] for f in security.findings(review(**ALL_TENS))] == ["critical", "low"]


def test_findings_keep_a_known_source():
    sourced = review(**ALL_TENS)
    sourced["findings"][0]["source"] = "Platform"
    sourced["findings"][1]["source"] = "the agent"
    assert {f["title"]: f["source"] for f in security.findings(sourced)} == {"No HSTS": "platform", "Token in logs": None}


def test_condensed_transcript(tmp_path):
    events = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Deploying now"},
                                                      {"type": "tool_use", "name": "Bash", "input": {"command": "vercel deploy --prod"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "x" * 2000}]}},
    ]
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps({"t": i, "e": e}) for i, e in enumerate(events)))
    text = security.condensed_transcript(path)
    assert "**Agent:** Deploying now" in text and "vercel deploy --prod" in text
    assert "Result (error)" in text and "500 more characters" in text
    assert "didn't run" in security.condensed_transcript(tmp_path / "missing.jsonl")


@pytest.fixture
def deployed_cell(tmp_path, monkeypatch):
    for name in ("GH_TOKEN", "GH_OWNER", "GITHUB_STEP_SUMMARY", "CLOUDISH_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "5-1", "vercel", "opus-5-5", "static", 1)
    (current.workspace / "server.js").write_text(f"const key = '{SECRET}';\n")
    current.write("verify.json", {"url": "https://adb-x.vercel.app", "readiness": {"ready": True}, "checks": []})
    current.write("deployment.json", {"url": "https://adb-x.vercel.app", "resources": []})
    return current


def fake_reviewer(tmp_path, body: str) -> str:
    script = tmp_path / "fake-reviewer"
    script.write_text(f"#!{sys.executable}\nimport json, pathlib, sys\nprompt = sys.stdin.read()\n" + textwrap.dedent(body)
                      + '\nprint(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3,'
                        ' "result": "done", "total_cost_usd": 0.42, "usage": {}, "modelUsage": {}}))\n')
    script.chmod(0o755)
    return str(script)


def test_review_step_scores_the_live_deployment(deployed_cell, tmp_path, monkeypatch):
    claude = fake_reviewer(tmp_path, f"""
        here = pathlib.Path(".")
        assert "https://adb-x.vercel.app" in prompt and "`least_privilege`" in prompt
        assert (here / "TASK.md").exists() and (here / "process" / "deploy.md").exists()
        assert "[REDACTED]" in (here / "app" / "server.js").read_text()   # secrets masked before review
        context = json.loads((here / "process" / "context.json").read_text())
        assert context["use"] == "commercial" and context["cloud"] == "Vercel"   # the static site is a company's
        criteria = {{c: {{"score": 8, "rationale": "ok"}} for c in
                    ("secrets", "provenance", "compliance", "least_privilege", "transport", "exposure", "application")}}
        (here / "security-review.json").write_text(json.dumps({{"criteria": criteria, "findings": [], "summary": "Good."}}))
        """)
    monkeypatch.setenv("BENCH_CLAUDE_BIN", claude)
    report = cell.review(deployed_cell)
    assert report["status"] == "completed" and report["score"] == 80
    assert report["reviewer"]["model"] == "claude-opus-5-5" and report["reviewer"]["cost_usd"] == pytest.approx(0.42)
    record = result.build(deployed_cell)
    record["code"] = {}
    assert record["security"]["score"] == 80
    assert "**80/100**" in result.render_report(record, deployed_cell)


def test_review_without_a_result_file_is_an_error(deployed_cell, tmp_path, monkeypatch):
    monkeypatch.setenv("BENCH_CLAUDE_BIN", fake_reviewer(tmp_path, "pass"))
    report = cell.review(deployed_cell)
    assert report["status"] == "error" and "security-review.json" in report["detail"]


def test_nothing_to_review_without_a_deployment(deployed_cell):
    deployed_cell.write("verify.json", {"url": None, "readiness": {"ready": False}, "checks": []})
    assert cell.review(deployed_cell)["status"] == "skipped"
