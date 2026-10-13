"""Vercel (https://vercel.com): projects with usage-billed functions, plus team-level storage."""

from __future__ import annotations

import re
from typing import Any, Iterator

from bench.clouds.base import Cloud, Resource, api_for, load_pricing
from bench.clouds.http import Api, ApiError

API = "https://api.vercel.com"
BLOB_API = "https://vercel.com"
BLOB_API_VERSION = "12"  # what @vercel/blob 2.x sends
ENV_TARGETS = ("development", "production", "preview")
MAX_BLOB_BATCHES = 100  # of 1,000 blobs; a benchmark store holds a handful


class Vercel(Cloud):
    id = "vercel"
    credentials = ("VERCEL_TOKEN",)
    # Stores are disconnected from projects before deletion, so delete them first.
    delete_order = ("integration_store", "blob_store", "global_config", "project")

    def __init__(self, env) -> None:
        super().__init__(env)
        self.api = api_for(API, env.get("VERCEL_TOKEN", ""))
        self.blob = Api(BLOB_API, {})  # authenticated per store, see _blob_headers
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
            # Vercel refuses to delete a store that still holds blobs (HTTP 409 not_empty).
            self._empty_blob_store(resource, scope)
            self.api.delete(f"/v1/storage/stores/{resource.id}/connections", params=scope)
            self.api.delete(f"/v1/storage/stores/blob/{resource.id}", params=scope)
        elif resource.kind == "global_config":
            self.api.delete(f"/v1/global-config/{resource.id}", params=scope)
        elif resource.kind == "integration_store":
            self.api.delete(f"/v1/storage/stores/{resource.id}/connections", params=scope)
            self.api.delete(f"/v1/storage/stores/integration/{resource.id}", params=scope)

    def _empty_blob_store(self, store: Resource, scope: dict[str, str]) -> None:
        """Deletes every blob in a store, like `vercel blob empty-store`. The Blob API only accepts the
        store's own credentials, so they come from the environment of a project connected to it (as
        `vercel env pull` gets them), or else of a temporary project connected just for this."""
        connections = (self.api.get(f"/v1/storage/stores/{store.id}/connections", **scope) or {}).get("connections") or []
        projects = {c.get("projectId") or (c.get("project") or {}).get("id") for c in connections} - {None}
        headers = next(filter(None, (self._blob_headers(project, store.id, scope) for project in sorted(projects))), None)
        temporary = None
        try:
            if headers is None:
                temporary = self.api.request("POST", "/v11/projects", params=scope,
                                             json={"name": temporary_project_name(store.name)})["id"]
                self.api.request("POST", f"/v1/storage/stores/{store.id}/connections", params=scope,
                                 json={"projectId": temporary, "envVarEnvironments": ["development"]})
                headers = self._blob_headers(temporary, store.id, scope)
            if headers is None:
                raise RuntimeError("found no credentials to empty the Blob store")
            for _ in range(MAX_BLOB_BATCHES):
                listing = self.blob.request("GET", "/api/blob", params={"limit": 1000}, headers=headers) or {}
                urls = [blob["url"] for blob in listing.get("blobs") or []]
                if not urls:
                    return
                self.blob.request("POST", "/api/blob/delete", json={"urls": urls}, headers=headers)
            raise RuntimeError(f"the Blob store still holds blobs after {MAX_BLOB_BATCHES} batches of deletes")
        finally:
            if temporary:
                self.api.delete(f"/v9/projects/{temporary}", params=scope)

    def _blob_headers(self, project_id: str, store_id: str, scope: dict[str, str]) -> dict[str, str] | None:
        for target in ENV_TARGETS:
            try:
                env = (self.api.get(f"/v3/env/pull/{project_id}/{target}", **scope) or {}).get("env") or {}
            except ApiError:
                continue
            if headers := blob_headers(env, store_id):
                return headers
        return None

    def account(self) -> dict[str, Any]:
        plans = {}
        for team in self.teams():
            if team.get("id"):
                info = self.api.get(f"/v2/teams/{team['id']}") or {}
                plans[team["id"]] = (info.get("billing") or {}).get("plan")
        return {"team_plans": plans}


def blob_headers(env: dict[str, Any], store_id: str) -> dict[str, str] | None:
    """Blob API headers from a project's pulled environment: the store's read-write token
    (vercel_blob_rw_<store>_<secret>), or the project's OIDC token when the store is connected by OIDC."""
    store = store_id.removeprefix("store_")
    for value in map(str, env.values()):
        parts = value.split("_")
        if value.startswith("vercel_blob_rw_") and len(parts) > 4 and parts[3].lower() == store.lower():
            return {"Authorization": f"Bearer {value}", "x-vercel-blob-store-id": parts[3],
                    "x-api-version": BLOB_API_VERSION}
    connected = {str(value).removeprefix("store_").lower() for name, value in env.items() if name.endswith("STORE_ID")}
    if env.get("VERCEL_OIDC_TOKEN") and store.lower() in connected:
        return {"Authorization": f"Bearer {env['VERCEL_OIDC_TOKEN']}", "x-vercel-blob-store-id": store,
                "x-api-version": BLOB_API_VERSION}
    return None


def temporary_project_name(store_name: str) -> str:
    """Keeps the store's name, and with it the cell prefix, so a leftover is found and deleted."""
    base = re.sub(r"[^a-z0-9._-]+", "-", store_name.lower()).strip("-") or "store"
    return re.sub(r"-{3,}", "--", f"{base[:80]}-teardown")


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
