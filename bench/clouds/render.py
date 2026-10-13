"""Render (https://render.com): services, Postgres and Key Value instances on fixed monthly plans."""

from __future__ import annotations

from typing import Any, Iterator

from bench.clouds.base import Cloud, Resource, api_for, load_pricing, lookup_plan

API = "https://api.render.com/v1"
PAGE = 100


class Render(Cloud):
    id = "render"
    credentials = ("RENDER_API_KEY",)
    delete_order = ("service", "postgres", "key_value", "env_group", "registry_credential", "project")

    def __init__(self, env) -> None:
        super().__init__(env)
        self.api = api_for(API, env.get("RENDER_API_KEY", ""))
        self._owners: list[str] | None = None

    def owners(self) -> list[str]:
        """Every workspace the key can see: an agent may create resources in any of them, and the
        cell's unique prefix keeps the scan safe."""
        if self._owners is None:
            owners = [o["owner"]["id"] for o in self._pages("/owners")]
            configured = self.env.get("RENDER_OWNER_ID")
            self._owners = owners + ([configured] if configured and configured not in owners else [])
        return self._owners

    def _pages(self, path: str, **params: Any) -> Iterator[dict[str, Any]]:
        """Follows Render's cursor pagination; list items look like {"<kind>": {...}, "cursor": "..."}."""
        cursor = None
        while True:
            page = self.api.get(path, limit=PAGE, cursor=cursor, **params) or []
            yield from page
            if len(page) < PAGE or not page[-1].get("cursor"):
                return
            cursor = page[-1]["cursor"]

    def list_resources(self) -> list[Resource]:
        try:
            owners = self.owners()
        except Exception as error:
            self.errors.append(f"listing workspaces failed: {error}")
            return []
        resources = []
        for owner in owners:
            resources += self.collect("services", lambda: self._services(owner))
            resources += self.collect("postgres", lambda: self._datastores(owner, "/postgres", "postgres", "postgres"))
            resources += self.collect("key value", lambda: self._datastores(owner, "/key-value", "keyValue", "key_value"))
            resources += self.collect("env groups", lambda: self._bare(owner, "/env-groups", "env_group"))
            resources += self.collect("registry credentials", lambda: self._bare(owner, "/registrycredentials", "registry_credential"))
            resources += self.collect("projects", lambda: self._datastores(owner, "/projects", "project", "project"))
        return resources

    def _services(self, owner: str) -> Iterator[Resource]:
        for item in self._pages("/services", ownerId=owner, includePreviews="false"):
            service = item["service"]
            details = service.get("serviceDetails") or {}
            yield Resource(
                kind="service",
                id=service["id"],
                name=service["name"],
                created_at=service.get("createdAt"),
                plan=details.get("plan"),
                url=details.get("url"),
                details={
                    "type": service.get("type"),
                    "instances": details.get("numInstances") or 1,
                    "disk_gb": (details.get("disk") or {}).get("sizeGB"),
                    "runtime": details.get("runtime") or details.get("env"),
                    "region": details.get("region"),
                    "suspended": service.get("suspended"),
                    "source": service.get("repo") or service.get("imagePath"),
                },
            )

    def _datastores(self, owner: str, path: str, key: str, kind: str) -> Iterator[Resource]:
        for item in self._pages(path, ownerId=owner):
            data = item[key]
            yield Resource(
                kind=kind,
                id=data["id"],
                name=data["name"],
                created_at=data.get("createdAt"),
                plan=data.get("plan"),
                details={"disk_gb": data.get("diskSizeGB"), "status": data.get("status"), "expires_at": data.get("expiresAt")},
            )

    def _bare(self, owner: str, path: str, kind: str) -> Iterator[Resource]:
        for data in self.api.get(path, ownerId=owner, limit=PAGE) or []:
            data = data.get("envGroup", data) if isinstance(data, dict) else {}
            if data.get("id"):
                yield Resource(kind=kind, id=data["id"], name=data.get("name", ""), created_at=data.get("createdAt"))

    def price(self, resources: list[Resource]) -> None:
        table = load_pricing(self.id)
        for r in resources:
            if r.kind == "service":
                service_type = r.details.get("type")
                if service_type == "static_site":
                    r.monthly_usd, r.pricing = 0.0, "static sites are free"
                elif service_type == "cron_job":
                    r.monthly_usd, r.pricing = float(table["cron_job_minimum"]), "cron job minimum; billed per minute run"
                else:
                    base = lookup_plan(table["services"], r.plan)
                    if base is not None:
                        disk = float(r.details.get("disk_gb") or 0) * table["disk_per_gb"]
                        r.monthly_usd = round(base * int(r.details.get("instances") or 1) + disk, 2)
                        r.pricing = f"{r.plan} x {r.details.get('instances') or 1} instance(s)" + (f" + {r.details['disk_gb']} GB disk" if disk else "")
            elif r.kind == "postgres":
                base = lookup_plan(table["postgres"], r.plan)
                if base is not None:
                    storage = 0.0
                    if (r.plan or "").lower() not in table["postgres_storage_included"]:
                        storage = float(r.details.get("disk_gb") or 1) * table["postgres_storage_per_gb"]
                    r.monthly_usd = round(base + storage, 2)
                    r.pricing = f"Postgres {r.plan}" + (f" + {r.details.get('disk_gb') or 1} GB storage" if storage else "")
            elif r.kind == "key_value":
                if (base := lookup_plan(table["key_value"], r.plan)) is not None:
                    r.monthly_usd, r.pricing = base, f"Key Value {r.plan}"
            else:
                r.monthly_usd, r.pricing = 0.0, "no charge"
            if r.monthly_usd is None:
                r.pricing = f"unknown plan {r.plan!r}"

    def delete(self, resource: Resource) -> None:
        path = {
            "service": "/services",
            "postgres": "/postgres",
            "key_value": "/key-value",
            "env_group": "/env-groups",
            "registry_credential": "/registrycredentials",
            "project": "/projects",
        }[resource.kind]
        self.api.delete(f"{path}/{resource.id}")

    def account(self) -> dict[str, Any]:
        return {"workspaces": self.owners()}
