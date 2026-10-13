"""Cloudish (https://cloudish.ai): container projects billed per second from prepaid credits."""

from __future__ import annotations

from typing import Any, Iterable

from bench.clouds.base import HOURS_PER_MONTH, Cloud, Resource, api_for, load_pricing

API = "https://cloudish.ai/api/v1"


def find_key(data: Any, *names: str) -> Any:
    """Depth-first search for the first of `names` in nested dicts (the API wraps objects variously)."""
    if isinstance(data, dict):
        for name in names:
            if data.get(name) not in (None, ""):
                return data[name]
        for value in data.values():
            if (found := find_key(value, *names)) is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            if (found := find_key(value, *names)) is not None:
                return found
    return None


def items(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get(key), list):
        return payload[key]
    return []


class Cloudish(Cloud):
    id = "cloudish"
    credentials = ("CLOUDISH_API_KEY",)
    delete_order = ("project",)

    def __init__(self, env) -> None:
        super().__init__(env)
        self.api = api_for(API, env.get("CLOUDISH_API_KEY", ""))

    def list_resources(self) -> list[Resource]:
        return self.collect("projects", self._projects)

    def _projects(self) -> Iterable[Resource]:
        for project in items(self.api.get("/projects"), "projects"):
            path = project.get("path") or f"{(project.get('owner') or {}).get('alias')}/{project.get('name')}"
            detail = self.api.request("GET", f"/projects/{path}", ok_missing=True) or {}
            subdomain = find_key(detail, "subdomain") or {}
            yield Resource(
                kind="project",
                id=path,
                name=str(project.get("name") or path.split("/")[-1]),
                # Only the project's own timestamp: a nested one may belong to a newer build.
                created_at=project.get("created_at") or project.get("createdAt"),
                url=(subdomain.get("url") if isinstance(subdomain, dict) else None) or find_key(detail, "url"),
                details={
                    "cpuCores": find_key(detail, "cpuCores", "cpu_cores"),
                    "memoryGb": find_key(detail, "memoryGb", "memory_gb"),
                    "replicas": find_key(detail, "replicas"),
                    "status": find_key(detail, "status"),
                    "volume_enabled": find_key(detail, "volumeEnabled", "volume_enabled"),
                    "access": project.get("access"),
                },
            )

    def price(self, resources: list[Resource]) -> None:
        fallback = load_pricing(self.id)
        try:
            live = self.api.get("/pricing")
            source = "live GET /api/v1/pricing"
        except Exception:
            live, source = fallback["pricing"], "fallback table in bench/clouds/pricing/cloudish.yaml"
        defaults = (live.get("defaults") or {}).get("docker") or {"cpuCores": 0.5, "memoryGb": 1}
        for resource in resources:
            cpu = float(resource.details.get("cpuCores") or defaults["cpuCores"])
            memory = float(resource.details.get("memoryGb") or defaults["memoryGb"])
            replicas = int(resource.details.get("replicas") or 1)
            hourly = credits_per_hour(live, cpu, memory) * float((live.get("credit") or {}).get("usd", 1))
            size = f"{cpu:g} CPU / {memory:g} GB"
            resource.plan = next((i["name"] for i in live.get("instances", [])
                                  if float(i["cpuCores"]) == cpu and float(i["memoryGb"]) == memory), size)
            resource.monthly_usd = round(hourly * HOURS_PER_MONTH * replicas, 2)
            resource.pricing = (f"{size} x {replicas} replica(s) running 730 h/month ({source}); "
                                "billed per second and scales to zero when idle, so idle apps cost less")

    def delete(self, resource: Resource) -> None:
        self.api.delete(f"/projects/{resource.id}")

    def account(self) -> dict[str, Any]:
        credits = self.api.get("/credits")
        return {"balance_usd": credits.get("balance") if isinstance(credits, dict) else None}


def credits_per_hour(pricing: dict[str, Any], cpu: float, memory: float) -> float:
    for instance in pricing.get("instances", []):
        if float(instance["cpuCores"]) == cpu and float(instance["memoryGb"]) == memory:
            return float(instance["creditsPerHour"])
    rates = pricing["compute"]
    per_second = cpu * rates["rateCpuCorePerSecond"] + memory * rates["rateMemGbPerSecond"] + rates["rateFlatPerSecond"]
    return per_second * (1 + rates.get("profitMargin", 0)) * 3600
