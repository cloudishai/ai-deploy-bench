"""DigitalOcean (https://www.digitalocean.com): App Platform apps plus the IaaS products an agent
might reach for instead (Droplets, managed databases, registries, functions, ...)."""

from __future__ import annotations

from typing import Any, Iterator

from bench.clouds.base import Cloud, Resource, api_for, load_pricing, lookup_plan

API = "https://api.digitalocean.com/v2"
SERVICE_COMPONENTS = ("services", "workers")


class DigitalOcean(Cloud):
    id = "digitalocean"
    credentials = ("DIGITALOCEAN_ACCESS_TOKEN",)
    delete_order = (
        "app", "kubernetes_cluster", "load_balancer", "droplet", "database", "volume",
        "functions_namespace", "registry", "spaces_key", "project",
    )

    def __init__(self, env) -> None:
        super().__init__(env)
        # Some DELETEs (projects) answer 415 without a JSON content type, even with no body.
        self.api = api_for(API, env.get("DIGITALOCEAN_ACCESS_TOKEN", ""), **{"Content-Type": "application/json"})

    def _pages(self, path: str, key: str, **params: Any) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            payload = self.api.get(path, page=page, per_page=200, **params) or {}
            yield from payload.get(key) or []
            if not ((payload.get("links") or {}).get("pages") or {}).get("next"):
                return
            page += 1

    def list_resources(self) -> list[Resource]:
        sources = {
            "apps": self._apps,
            "databases": lambda: self._simple("/databases", "databases", "database", plan="size",
                                              extra=("engine", "num_nodes", "status")),
            "droplets": self._droplets,
            "volumes": lambda: self._simple("/volumes", "volumes", "volume", extra=("size_gigabytes",)),
            "load balancers": lambda: self._simple("/load_balancers", "load_balancers", "load_balancer",
                                                   extra=("size_unit", "type")),
            "kubernetes": lambda: self._simple("/kubernetes/clusters", "kubernetes_clusters", "kubernetes_cluster",
                                               extra=("node_pools",)),
            "functions": self._functions,
            "registries": self._registries,
            "spaces keys": self._spaces_keys,
            "projects": self._projects,
        }
        resources = []
        for kind, fetch in sources.items():
            resources += self.collect(kind, fetch)
        return resources

    def _apps(self) -> Iterator[Resource]:
        for app in self._pages("/apps", "apps"):
            spec = app.get("spec") or {}
            yield Resource(
                kind="app",
                id=app["id"],
                name=spec.get("name", ""),
                created_at=app.get("created_at"),
                url=app.get("live_url") or app.get("default_ingress"),
                details={"spec": spec, "region": (app.get("region") or {}).get("slug")},
            )

    def _simple(self, path: str, key: str, kind: str, plan: str | None = None, extra: tuple[str, ...] = ()) -> Iterator[Resource]:
        for item in self._pages(path, key):
            yield Resource(
                kind=kind,
                id=str(item["id"]),
                name=item.get("name", ""),
                created_at=item.get("created_at"),
                plan=item.get(plan) if plan else None,
                details={field: item.get(field) for field in extra},
            )

    def _droplets(self) -> Iterator[Resource]:
        for droplet in self._pages("/droplets", "droplets"):
            size = droplet.get("size") or {}
            yield Resource(
                kind="droplet",
                id=str(droplet["id"]),
                name=droplet.get("name", ""),
                created_at=droplet.get("created_at"),
                plan=droplet.get("size_slug") or size.get("slug"),
                details={"price_monthly": size.get("price_monthly")},
            )

    def _functions(self) -> Iterator[Resource]:
        for ns in (self.api.get("/functions/namespaces") or {}).get("namespaces") or []:
            yield Resource(kind="functions_namespace", id=ns["namespace"], name=ns.get("label", ""),
                           created_at=ns.get("created_at"))

    def _registries(self) -> Iterator[Resource]:
        payload = self.api.get("/registries") or {}
        tier = None
        if payload.get("registries"):
            subscription = (self.api.get("/registries/subscription") or {}).get("subscription") or {}
            tier = (subscription.get("tier") or {}).get("slug")
        for registry in payload.get("registries") or []:
            yield Resource(kind="registry", id=registry["name"], name=registry["name"],
                           created_at=registry.get("created_at"), plan=tier)

    def _spaces_keys(self) -> Iterator[Resource]:
        for key in (self.api.get("/spaces/keys") or {}).get("keys") or []:
            yield Resource(kind="spaces_key", id=key["access_key"], name=key.get("name", ""),
                           created_at=key.get("created_at"))

    def _projects(self) -> Iterator[Resource]:
        for project in self._pages("/projects", "projects"):
            if project.get("is_default"):
                continue
            yield Resource(kind="project", id=project["id"], name=project.get("name", ""),
                           created_at=project.get("created_at"))

    def price(self, resources: list[Resource]) -> None:
        table = load_pricing(self.id)
        sizes = dict(table["app_platform"]["instance_sizes"])
        try:
            live = self.api.get("/apps/tiers/instance_sizes") or {}
            sizes.update({s["slug"]: float(s["usd_per_month"]) for s in live.get("instance_sizes") or []})
        except Exception as error:
            self.errors.append(f"instance size prices unavailable, using fallback table: {error}")
        for r in resources:
            if r.kind == "app":
                r.monthly_usd, r.pricing, r.plan = app_cost(r.details.get("spec") or {}, sizes, table["app_platform"])
            elif r.kind == "database":
                engine_prices = table["databases"].get(str(r.details.get("engine")), {})
                if (node := lookup_plan(engine_prices, r.plan)) is not None:
                    nodes = int(r.details.get("num_nodes") or 1)
                    r.monthly_usd, r.pricing = round(node * nodes, 2), f"{r.details.get('engine')} {r.plan} x {nodes} node(s)"
            elif r.kind == "droplet" and r.details.get("price_monthly") is not None:
                r.monthly_usd, r.pricing = float(r.details["price_monthly"]), f"Droplet {r.plan}"
            elif r.kind == "volume":
                gb = float(r.details.get("size_gigabytes") or 0)
                r.monthly_usd, r.pricing = round(gb * table["volume_per_gb"], 2), f"{gb:g} GB volume"
            elif r.kind == "load_balancer":
                nodes = int(r.details.get("size_unit") or 1)
                r.monthly_usd, r.pricing = nodes * table["load_balancer_per_node"], f"load balancer x {nodes} node(s)"
            elif r.kind == "registry":
                if (tier := lookup_plan(table["registry_tiers"], r.plan)) is not None:
                    r.monthly_usd, r.pricing = tier, f"Container Registry {r.plan} tier (one per account)"
            elif r.kind in ("functions_namespace", "spaces_key", "project"):
                r.monthly_usd, r.pricing = 0.0, "no charge at benchmark usage"
            if r.monthly_usd is None and not r.pricing:
                r.pricing = "price unknown"

    def delete(self, resource: Resource) -> None:
        if resource.kind == "kubernetes_cluster":
            self.api.delete(f"/kubernetes/clusters/{resource.id}/destroy_with_associated_resources/dangerous",
                            headers={"X-Dangerous": "true"})
            return
        path = {
            "app": "/apps",
            "load_balancer": "/load_balancers",
            "droplet": "/droplets",
            "database": "/databases",
            "volume": "/volumes",
            "functions_namespace": "/functions/namespaces",
            "registry": "/registries",
            "spaces_key": "/spaces/keys",
            "project": "/projects",
        }[resource.kind]
        self.api.delete(f"{path}/{resource.id}")


def app_cost(spec: dict[str, Any], sizes: dict[str, float], table: dict[str, Any]) -> tuple[float | None, str, str]:
    """Monthly cost of an App Platform app from its spec: (usd, explanation, plan summary)."""
    parts, total, unknown = [], 0.0, []
    for kind in SERVICE_COMPONENTS:
        for component in spec.get(kind) or []:
            slug = component.get("instance_size_slug") or "apps-s-1vcpu-0.5gb"
            count = int((component.get("autoscaling") or {}).get("min_instance_count") or component.get("instance_count") or 1)
            if slug in sizes:
                total += sizes[slug] * count
                parts.append(f"{component.get('name')}: {slug} x {count}")
            else:
                unknown.append(slug)
    for database in spec.get("databases") or []:
        if not database.get("production") and not database.get("cluster_name"):
            total += table["dev_database"]
            parts.append(f"{database.get('name')}: dev database")
    if (spec.get("egress") or {}).get("type") == "DEDICATED_IP":
        total += table["dedicated_egress_ip"]
        parts.append("dedicated egress IP")
    static_only = not parts and not unknown and bool(spec.get("static_sites") or spec.get("functions"))
    if static_only:
        return float(table["static_only_app"]), "static-only app: first 3 per team are free, then $3/month", "static"
    if unknown:
        return None, f"unknown instance sizes {unknown}", ", ".join(parts)
    return round(total, 2), "; ".join(parts) or "no billable components", ", ".join(parts)
