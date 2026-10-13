"""Vercel (https://vercel.com): projects with usage-billed functions, plus team-level storage."""

from __future__ import annotations

from typing import Any, Iterator

from bench.clouds.base import Cloud, Resource, api_for, load_pricing

API = "https://api.vercel.com"


class Vercel(Cloud):
    id = "vercel"
    credentials = ("VERCEL_TOKEN",)
    # Stores are disconnected from projects before deletion, so delete them first.
    delete_order = ("integration_store", "blob_store", "global_config", "project")

    def __init__(self, env) -> None:
        super().__init__(env)
        self.api = api_for(API, env.get("VERCEL_TOKEN", ""))
        self._teams: list[dict[str, Any]] | None = None

    def teams(self) -> list[dict[str, Any]]:
        """Every scope the token can see, plus the personal one ({}): an agent may deploy to any of
        them, and the cell's unique prefix keeps the scan safe."""
        if self._teams is None:
            teams = (self.api.get("/v2/teams", limit=100) or {}).get("teams") or []
            configured = self.env.get("VERCEL_TEAM_ID")
            if configured and all(t.get("id") != configured for t in teams):
                teams.append({"id": configured})
            self._teams = teams + [{}]
        return self._teams

    def _scope(self, team: dict[str, Any]) -> dict[str, str]:
        return {"teamId": team["id"]} if team.get("id") else {}

    def list_resources(self) -> list[Resource]:
        try:
            teams = self.teams()
        except Exception as error:
            self.errors.append(f"listing teams failed: {error}")
            return []
        resources: dict[str, Resource] = {}
        for team in teams:
            for resource in (self.collect("projects", lambda: self._projects(team))
                             + self.collect("storage stores", lambda: self._stores(team))
                             + self.collect("global config", lambda: self._global_configs(team))):
                # The personal scope can alias the default team; keep the first (team-scoped) copy.
                resources.setdefault(resource.id, resource)
        return list(resources.values())

    def _projects(self, team: dict[str, Any]) -> Iterator[Resource]:
        until = None
        while True:
            payload = self.api.get("/v10/projects", limit=100, until=until, **self._scope(team))
            projects = payload if isinstance(payload, list) else (payload or {}).get("projects", [])
            for project in projects:
                yield Resource(
                    kind="project",
                    id=project["id"],
                    name=project["name"],
                    created_at=project.get("createdAt"),
                    url=production_url(project),
                    details={"team_id": team.get("id"), "framework": project.get("framework")},
                )
            until = (payload.get("pagination") or {}).get("next") if isinstance(payload, dict) else None
            if not until or not projects:
                return

    def _stores(self, team: dict[str, Any]) -> Iterator[Resource]:
        # Undocumented but used by the Vercel CLI; lists Blob and Marketplace stores.
        for store in (self.api.get("/v1/storage/stores", **self._scope(team)) or {}).get("stores", []):
            if store.get("type") not in ("blob", "integration"):
                continue  # Edge/Global Config stores are listed by _global_configs
            kind = "blob_store" if store.get("type") == "blob" else "integration_store"
            yield Resource(
                kind=kind,
                id=store["id"],
                name=store.get("name", ""),
                created_at=store.get("createdAt"),
                plan=_plan_name(store.get("billingPlan")),
                details={"team_id": team.get("id"), "product": (store.get("product") or {}).get("slug"),
                         "billing_plan": store.get("billingPlan")},
            )

    def _global_configs(self, team: dict[str, Any]) -> Iterator[Resource]:
        payload = self.api.get("/v1/global-config", **self._scope(team)) or []
        for config in payload if isinstance(payload, list) else []:
            yield Resource(kind="global_config", id=config["id"], name=config.get("slug", ""),
                           created_at=config.get("createdAt"), details={"team_id": team.get("id")})

    def price(self, resources: list[Resource]) -> None:
        table = load_pricing(self.id)
        for r in resources:
            if r.kind == "project":
                r.monthly_usd, r.pricing = float(table["project"]), "no fixed fee; usage within the plan's included allowance"
            elif r.kind == "blob_store":
                r.monthly_usd, r.pricing = float(table["blob_store"]), "usage-billed; free within plan allowance"
            elif r.kind == "global_config":
                r.monthly_usd, r.pricing = float(table["global_config"]), "usage-billed; free within plan allowance"
            elif r.kind == "integration_store":
                price = _plan_price(r.details.get("billing_plan"))
                if price is not None:
                    r.monthly_usd, r.pricing = price, f"Marketplace plan {r.plan or '?'} ({r.details.get('product')})"
                else:
                    r.pricing = f"Marketplace plan {r.plan or '?'} ({r.details.get('product')}): price not reported"

    def delete(self, resource: Resource) -> None:
        scope = {"teamId": resource.details["team_id"]} if resource.details.get("team_id") else {}
        if resource.kind == "project":
            self.api.delete(f"/v9/projects/{resource.id}", params=scope)
        elif resource.kind == "blob_store":
            self.api.delete(f"/v1/storage/stores/{resource.id}/connections", params=scope)
            self.api.delete(f"/v1/storage/stores/blob/{resource.id}", params=scope)
        elif resource.kind == "global_config":
            self.api.delete(f"/v1/global-config/{resource.id}", params=scope)
        elif resource.kind == "integration_store":
            self.api.delete(f"/v1/storage/stores/{resource.id}/connections", params=scope)
            self.api.delete(f"/v1/storage/stores/integration/{resource.id}", params=scope)

    def account(self) -> dict[str, Any]:
        plans = {}
        for team in self.teams():
            if team.get("id"):
                info = self.api.get(f"/v2/teams/{team['id']}") or {}
                plans[team["id"]] = (info.get("billing") or {}).get("plan")
        return {"team_plans": plans}


def production_url(project: dict[str, Any]) -> str | None:
    """The public production alias; the per-deployment URL is often behind Vercel Authentication."""
    production = (project.get("targets") or {}).get("production") or {}
    aliases = production.get("alias") or []
    if aliases:
        return f"https://{aliases[0]}"
    return f"https://{production['url']}" if production.get("url") else None


def _plan_name(plan: Any) -> str | None:
    if isinstance(plan, dict):
        return plan.get("name") or plan.get("id") or plan.get("type")
    return plan if isinstance(plan, str) else None


def _plan_price(plan: Any) -> float | None:
    if not isinstance(plan, dict):
        return None
    if str(plan.get("type", "")).lower() == "free" or "free" in str(plan.get("name", "")).lower():
        return 0.0
    for key in ("cost", "price", "monthlyPrice"):
        value = plan.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip("$").split()[0])
            except (ValueError, IndexError):
                continue
    return None
