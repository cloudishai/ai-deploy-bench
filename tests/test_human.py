import json

import pytest

from bench import aggregate, cell, config, human, prompts, result


@pytest.fixture
def make_cell(tmp_path):
    def make(cloud: str, app: str = "crud"):
        return cell.prepare(tmp_path / f"cell-{cloud}", tmp_path / f"work-{cloud}", "7-1", cloud, "opus-5-5", app, 1)
    return make


def write_transcript(current, events):
    lines = [json.dumps({"t": i, "e": event}) for i, event in enumerate(events)]
    current.write("deploy/phase.json", {"name": "deploy", "status": "completed"})
    (current.dir / "deploy" / "transcript.jsonl").write_text("\n".join(lines) + "\n")


def tool_result(text):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": text}]}}


def ids(assessment):
    return [s["id"] for s in assessment["steps"]]


def test_classify_maps_free_text_to_catalog_steps():
    assert human.classify("Add a credit card to the Render workspace") == "payment_method"
    assert human.classify("Accept the Neon integration terms in the Vercel dashboard") == "accept_integration_terms"
    assert human.classify("Claim the API key and add credits") == "add_credits"
    assert human.classify("Create a GitHub repository Render can deploy from") == "git_hosting"
    assert human.classify("Reboot the router") == "other"


def test_cloudish_needs_no_person(make_cell):
    current = make_cell("cloudish")
    assessment = human.assess(current, {}, {"human_steps": []}, succeeded=True)
    assert (assessment["count"], assessment["minutes"], assessment["blocked"]) == (0, 0, False)


def test_blocked_deploy_counts_prerequisites_and_blockers(make_cell):
    current = make_cell("vercel")
    write_transcript(current, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Provisioning Neon"}]}},
        tool_result('{"status":"action_required","reason":"integration_terms_acceptance_required",'
                    '"verification_uri":"https://vercel.com/team/~/integrations/accept-terms/neon"}'),
    ])
    deployment = {"human_steps": [{"step": "Accept the Neon terms", "why": "Postgres for todos", "blocking": True}]}
    assessment = human.assess(current, {}, deployment, succeeded=False)
    assert ids(assessment) == ["signup", "api_token", "accept_integration_terms"]
    assert assessment["minutes"] == 3 + 2 + 3
    assert assessment["blocked"]
    terms = assessment["steps"][2]["evidence"]
    assert any(e.startswith("agent:") for e in terms) and any(e.startswith("tool output:") for e in terms)


def test_blockers_dont_count_when_the_agent_got_by_without_them(make_cell):
    current = make_cell("vercel")
    deployment = {"human_steps": [{"step": "Accept the Neon terms", "blocking": True}]}
    assessment = human.assess(current, {}, deployment, succeeded=True)
    assert ids(assessment) == ["signup", "api_token"] and not assessment["blocked"]
    assert assessment["blockers"][0]["id"] == "accept_integration_terms"  # still reported


def test_agent_prose_cannot_trigger_detection(make_cell):
    current = make_cell("vercel")
    write_transcript(current, [{"type": "assistant", "message": {"content": [
        {"type": "text", "text": "If I see integration_terms_acceptance_required I'll report it."}]}}])
    assert human.detected(current) == []


def test_resources_reveal_human_help(make_cell):
    render = make_cell("render")
    inventory = {
        "cloud": {"resources": [{"kind": "service", "name": "adb-x-web", "monthly_usd": 7.0}]},
        "github": {"resources": [{"kind": "repository", "name": "adb-x-web"}]},
    }
    assert ids(human.assess(render, inventory, {}, succeeded=True)) == ["signup", "api_token", "git_hosting", "payment_method"]
    vercel = make_cell("vercel")
    store = {"cloud": {"resources": [{"kind": "integration_store", "name": "adb-x-db", "monthly_usd": 0.0,
                                      "details": {"product": "neon"}}]}}
    assert "accept_integration_terms" in ids(human.assess(vercel, store, {}, succeeded=True))
    digitalocean = make_cell("digitalocean")
    paid = {"cloud": {"resources": [{"kind": "app", "name": "adb-x", "monthly_usd": 5.0}]}}
    assert ids(human.assess(digitalocean, paid, {}, succeeded=True)) == ["signup", "payment_method", "api_token"]


def test_blocked_cells_fail_at_the_human_stage(make_cell):
    current = make_cell("render", "static")
    current.write("verify.json", {"url": None, "success": False, "readiness": {"ready": False}, "checks": []})
    current.write("deployment.json", {"human_steps": [{"step": "Create a GitHub repository", "blocking": True}]})
    record = result.build(current)
    assert (record["status"], record["failure_stage"]) == ("failed", "human")
    assert "git_hosting" in [s["id"] for s in record["human"]["steps"]]
    record["code"] = {}
    assert "**Blocked:**" in result.render_report(record, current)


def test_cloudish_agents_never_receive_a_key(monkeypatch):
    cfg = config.load()
    monkeypatch.setenv("CLOUDISH_API_KEY", "cld_a_key_someone_made_by_hand")
    assert "CLOUDISH_API_KEY" not in cell.agent_env(cfg, cfg.cloud("cloudish"))
    prompt = prompts.deploy_prompt(cfg.cloud("cloudish"), cfg.app("static"), "adb-x-static", {"CLOUDISH_API_KEY": "cld_x"})
    assert "No credentials are provided for Cloudish." in prompt and "CLOUDISH_API_KEY" not in prompt


def test_human_setup_counts_each_step_once_per_cloud():
    cells = [
        {"human_steps": [{"id": "signup", "minutes": 3}, {"id": "api_token", "minutes": 2}]},
        {"human_steps": [{"id": "signup", "minutes": 3}, {"id": "accept_integration_terms", "minutes": 3}]},
    ]
    assert aggregate.human_setup(cells) == {"count": 3, "minutes": 8}


def test_saved_credentials_replace_a_skipped_inventory():
    skipped = {"skipped": "credentials not available", "resources": [], "monthly_usd": None}
    real = {"resources": [{"name": "adb-x"}], "monthly_usd": 21.66, "errors": []}
    assert cell.merge_inventories([skipped, real]) == real
    assert cell.merge_inventories([skipped]) == skipped
