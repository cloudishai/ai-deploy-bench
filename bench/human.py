"""Human steps: what a person had to do, or would have to do, for a cell's deployment to work.

Every step comes from evidence, never from assumptions about a cloud:

- prerequisites: the cloud's account setup in benchmark.yaml, which no agent can do for itself.
- used: things the deployment relies on that only exist because a person set them up, such as
  repositories in the GitHub scratch account, a Marketplace store (someone accepted its terms in a
  browser), or paid resources on a cloud whose paid plans need a payment method.
- blockers: steps the agent listed under `human_steps` in deployment.json, and provider errors in
  its tool output that only a person can resolve. They count only when the cell didn't succeed;
  an agent that deployed a working app evidently managed without them.

Minutes come from the `human_steps` catalog in benchmark.yaml.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from bench.cell import Cell

# Provider error messages that only a person can resolve. Matched against tool output only, so an
# agent paraphrasing its instructions can't trigger them.
TOOL_OUTPUT_BLOCKERS = {
    "accept_integration_terms": re.compile(r"integration_terms_acceptance_required"),  # Vercel CLI
    "payment_method": re.compile(r"must enter payment information|preauth_no_payment_method", re.I),  # Render
    "add_credits": re.compile(r"API key is out of credits", re.I),  # Cloudish
}
# Maps the agent's free-text description of a step to a catalog id; checked in order.
KEYWORDS = (
    ("payment_method", ("payment", "credit card", "billing")),
    ("accept_integration_terms", ("terms", "marketplace", "integration")),
    ("add_credits", ("credits", "claim", "top up", "balance")),
    ("git_hosting", ("github", "gitlab", "bitbucket", "git repo", "repository", "registry", "docker hub")),
    ("signup", ("sign up", "signup", "create an account", "verify", "account")),
    ("api_token", ("token", "api key", "credential")),
)


def classify(text: str) -> str:
    lowered = text.lower()
    for step, words in KEYWORDS:
        if any(word in lowered for word in words):
            return step
    return "other"


def reported(deployment: dict[str, Any]) -> list[dict[str, Any]]:
    """The agent's own list of things only a person can do."""
    steps = []
    for item in deployment.get("human_steps") or []:
        item = {"step": item} if isinstance(item, str) else item
        if not isinstance(item, dict):
            continue
        step, why = str(item.get("step") or "").strip(), str(item.get("why") or "").strip()
        text = f"{step} ({why})" if step and why else step or why
        if text:
            steps.append({"id": classify(text), "source": "agent", "detail": text[:300],
                          "blocking": item.get("blocking", True) is not False})
    return steps


def tool_output(cell: "Cell") -> Iterator[str]:
    path = cell.dir / "deploy" / "transcript.jsonl"
    if not path.exists():
        return
    with path.open(errors="ignore") as lines:
        for line in lines:
            try:
                event = json.loads(line).get("e") or {}
            except (ValueError, AttributeError):
                continue
            content = (event.get("message") or {}).get("content") if event.get("type") == "user" else None
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    inner = block.get("content")
                    if isinstance(inner, list):
                        inner = " ".join(b.get("text", "") for b in inner if isinstance(b, dict))
                    yield str(inner or "")


def detected(cell: "Cell") -> list[dict[str, Any]]:
    steps = {}
    for output in tool_output(cell):
        for step, pattern in TOOL_OUTPUT_BLOCKERS.items():
            if step not in steps and (match := pattern.search(output)):
                context = " ".join(output[max(0, match.start() - 100): match.end() + 100].split())
                steps[step] = {"id": step, "source": "tool output", "detail": context[:300], "blocking": True}
    return list(steps.values())


def used(inventory: dict[str, Any], prerequisites: tuple[str, ...], when_paid: tuple[str, ...]) -> list[dict[str, Any]]:
    """Steps evidenced by what the deployment is built on."""
    steps = []
    github = (inventory.get("github") or {}).get("resources") or []
    if github:
        steps.append({"id": "git_hosting", "source": "resources",
                      "detail": "used the GitHub scratch account: " + ", ".join(r["name"] for r in github[:5])})
    resources = (inventory.get("cloud") or {}).get("resources") or []
    stores = [r for r in resources if r.get("kind") == "integration_store"]
    if stores:
        steps.append({"id": "accept_integration_terms", "source": "resources", "detail": "Marketplace resources: "
                      + ", ".join(f"{r['name']} ({(r.get('details') or {}).get('product')})" for r in stores)})
    paid = [r for r in resources if (r.get("monthly_usd") or 0) > 0]
    for step in when_paid:
        if paid and step not in prerequisites:
            steps.append({"id": step, "source": "resources",
                          "detail": "paid resources: " + ", ".join(r["name"] for r in paid[:5])})
    return steps


def assess(cell: "Cell", inventory: dict[str, Any], deployment: dict[str, Any], succeeded: bool,
           harness_failed: bool = False) -> dict[str, Any]:
    cfg = cell.config
    cloud = cfg.cloud(cell.info["cloud"])
    catalog = cfg.human_steps
    blockers = reported(deployment) + detected(cell)
    counted = [{"id": step, "source": "prerequisite", "detail": "account setup"} for step in cloud.prerequisites]
    counted += used(inventory, cloud.prerequisites, cloud.when_paid)
    if not succeeded and not harness_failed:
        counted += [b for b in blockers if b["blocking"]]
    steps: dict[str, dict[str, Any]] = {}
    for step in counted:
        entry = catalog.get(step["id"]) or catalog.get("other") or {"minutes": 0, "description": step["id"]}
        target = steps.setdefault(step["id"], {"id": step["id"], "description": entry["description"],
                                               "minutes": entry["minutes"], "evidence": []})
        target["evidence"].append(f"{step['source']}: {step['detail']}")
    return {
        "steps": list(steps.values()),
        "count": len(steps),
        "minutes": sum(s["minutes"] for s in steps.values()),
        "blockers": blockers,
        "blocked": not succeeded and not harness_failed and any(b["blocking"] for b in blockers),
        "succeeded": succeeded,
    }
