"""Common interface for cloud adapters: find what a cell created, price it, and delete it.

Cells name every resource with a unique prefix, so an adapter lists the account's resources and
keeps those whose name starts with the prefix or that the agent declared in deployment.json.
Resources created during the cell that match neither are reported as possible leaks but never
deleted automatically, because the account may hold unrelated resources.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import time
from pathlib import Path
from typing import Any, Callable, ClassVar, Iterable, Mapping

import yaml

from bench.clouds.http import Api

PRICING_DIR = Path(__file__).parent / "pricing"
HOURS_PER_MONTH = 730


@dataclasses.dataclass
class Resource:
    kind: str
    id: str
    name: str
    created_at: str | None = None
    plan: str | None = None
    url: str | None = None
    monthly_usd: float | None = None
    pricing: str = ""
    matched_by: str = ""
    details: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def load_pricing(cloud_id: str) -> dict[str, Any]:
    return yaml.safe_load((PRICING_DIR / f"{cloud_id}.yaml").read_text())


def lookup_plan(table: Mapping[str, float], plan: str | None) -> float | None:
    """Finds a plan price, tolerating `-`/`_` and case differences between docs and APIs."""
    if not plan:
        return None
    for candidate in (plan, plan.lower(), plan.lower().replace("-", "_"), plan.lower().replace("_", "-")):
        if candidate in table:
            return float(table[candidate])
    return None


def parse_time(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):  # epoch seconds or milliseconds
        seconds = value / 1000 if value > 1e11 else value
        return dt.datetime.fromtimestamp(seconds, dt.timezone.utc)
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


class Cloud:
    id: ClassVar[str] = ""
    credentials: ClassVar[tuple[str, ...]] = ()
    # Kinds in the order they must be deleted (dependents first); unknown kinds go last.
    delete_order: ClassVar[tuple[str, ...]] = ()

    def __init__(self, env: Mapping[str, str]) -> None:
        self.env = env
        self.errors: list[str] = []

    def configured(self) -> bool:
        return all(self.env.get(name) for name in self.credentials)

    def list_resources(self) -> list[Resource]:
        raise NotImplementedError

    def price(self, resources: list[Resource]) -> None:
        """Fills `monthly_usd` and `pricing` on each resource."""

    def delete(self, resource: Resource) -> None:
        raise NotImplementedError

    def account(self) -> dict[str, Any]:
        return {}

    def collect(self, kind: str, fetch: Callable[[], Iterable[Resource]]) -> list[Resource]:
        """Runs one listing call, recording failures instead of aborting the whole inventory."""
        try:
            return list(fetch())
        except Exception as error:
            self.errors.append(f"listing {kind} failed: {error}")
            return []


def matches(resource: Resource, prefix: str, declared: Iterable[dict[str, Any]]) -> str:
    if resource.name.lower().startswith(prefix.lower()):
        return "prefix"
    for item in declared:
        if not isinstance(item, dict):
            continue
        if item.get("id") and str(item["id"]) == resource.id:
            return "declared"
        if item.get("name") and str(item["name"]) == resource.name:
            return "declared"
    return ""


def inventory(cloud: Cloud, prefix: str, declared: list[dict[str, Any]], since: str | None) -> dict[str, Any]:
    started = parse_time(since)
    owned, possible_leaks = [], []
    for resource in cloud.list_resources():
        if how := matches(resource, prefix, declared):
            resource.matched_by = how
            owned.append(resource)
        elif started and (created := parse_time(resource.created_at)) and created >= started:
            resource.matched_by = "created during cell"
            possible_leaks.append(resource)
    try:
        cloud.price(owned)
    except Exception as error:
        cloud.errors.append(f"pricing failed: {error}")
    priced = [r.monthly_usd for r in owned if r.monthly_usd is not None]
    return {
        "resources": [r.to_dict() for r in owned],
        "possible_leaks": [r.to_dict() for r in possible_leaks],
        "monthly_usd": round(sum(priced), 2) if owned else 0.0,
        "unpriced": [r.name for r in owned if r.monthly_usd is None],
        "account": _safe(cloud.account, cloud.errors),
        "errors": cloud.errors,
    }


def teardown(cloud: Cloud, resources: list[dict[str, Any]], retry_delay: float = 10.0) -> list[dict[str, Any]]:
    rank = {kind: i for i, kind in enumerate(cloud.delete_order)}
    pending = sorted((Resource(**r) for r in resources), key=lambda r: rank.get(r.kind, len(rank)))
    outcomes: dict[str, dict[str, Any]] = {}
    attempts = 3  # later attempts catch dependencies that weren't released yet
    for attempt in range(attempts):
        failed = []
        for resource in pending:
            try:
                cloud.delete(resource)
                outcomes[resource.id] = {"kind": resource.kind, "name": resource.name, "deleted": True}
            except Exception as error:
                outcomes[resource.id] = {"kind": resource.kind, "name": resource.name, "deleted": False, "error": str(error)[:500]}
                failed.append(resource)
        if not failed or attempt == attempts - 1:
            break
        pending = failed
        time.sleep(retry_delay * (attempt + 1))
    return list(outcomes.values())


def _safe(fn: Callable[[], dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    try:
        return fn()
    except Exception as error:
        errors.append(f"account lookup failed: {error}")
        return {}


def api_for(base_url: str, token: str, **headers: str) -> Api:
    return Api(base_url, {"Authorization": f"Bearer {token}", **headers})
