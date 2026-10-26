"""Railway (https://railway.com): projects of services, databases and volumes on infrastructure
Railway provisions and bills itself, metered per second. The GraphQL API at backboard.railway.com
lists the token's projects and deletes them; deleting a project removes its services and volumes."""

from __future__ import annotations

from typing import Any, Iterable

from bench.clouds.base import HOURS_PER_MONTH, Cloud, Resource, api_for, fixed_cost, load_pricing

API = "https://backboard.railway.com"
GRAPHQL_PATH = "/graphql/v2"

# A project's services and volumes. A volume's size lives on its volumeInstances (per environment),
# not on the Volume itself.
PROJECT_FIELDS = """
      edges { node {
        id name createdAt
        services { edges { node { id name } } }
        volumes { edges { node { id name volumeInstances { edges { node { currentSizeMB } } } } } }
      } }
"""
# `me.projects` only has the account's personal projects, and the CLI creates projects in a
# workspace, so each of the token's workspaces is listed as well.
WORKSPACES_QUERY = "query { me { workspaces { id } projects {" + PROJECT_FIELDS + "} } }"
WORKSPACE_PROJECTS_QUERY = "query($id: String!) { projects(workspaceId: $id) {" + PROJECT_FIELDS + "} }"
# A workspace token can't read `me`; its own projects are its workspace's.
TOKEN_PROJECTS_QUERY = "query { projects {" + PROJECT_FIELDS + "} }"
PROJECT_DELETE = "mutation($id: String!) { projectDelete(id: $id) }"


def nodes(connection: Any) -> list[dict[str, Any]]:
    """Unwraps a GraphQL `{edges: [{node: {...}}]}` connection into a list of nodes."""
    edges = (connection or {}).get("edges") or []
    return [edge["node"] for edge in edges if isinstance(edge, dict) and isinstance(edge.get("node"), dict)]


class Railway(Cloud):
    id = "railway"
    credentials = ("RAILWAY_API_TOKEN",)
    delete_order = ("project",)

    def __init__(self, env) -> None:
        super().__init__(env)
        self.api = api_for(API, env.get("RAILWAY_API_TOKEN", ""), **{"Content-Type": "application/json"})

    def gql(self, query: str, **variables: Any) -> dict[str, Any]:
        payload = self.api.request("POST", GRAPHQL_PATH, json={"query": query, "variables": variables}) or {}
        if payload.get("errors"):
            messages = "; ".join(e.get("message", "") for e in payload["errors"])
            raise RuntimeError(f"Railway API error: {messages}")
        return payload.get("data") or {}

    def list_resources(self) -> list[Resource]:
        return self.collect("projects", self._projects)

    def _projects(self) -> Iterable[Resource]:
        try:
            me = self.gql(WORKSPACES_QUERY).get("me") or {}
        except RuntimeError as error:
            if "Not Authorized" not in str(error):
                raise
            me = {"projects": self.gql(TOKEN_PROJECTS_QUERY).get("projects")}  # a workspace token
        projects = {p["id"]: p for p in nodes(me.get("projects"))}
        for workspace in me.get("workspaces") or []:
            data = self.gql(WORKSPACE_PROJECTS_QUERY, id=workspace["id"])
            projects.update({p["id"]: p for p in nodes(data.get("projects"))})
        for project in projects.values():
            services = nodes(project.get("services"))
            volumes = nodes(project.get("volumes"))
            volume_mb = sum((vi.get("currentSizeMB") or 0)
                            for v in volumes for vi in nodes(v.get("volumeInstances")))
            yield Resource(
                kind="project",
                id=project["id"],
                name=str(project.get("name") or project["id"]),
                created_at=project.get("createdAt"),
                details={
                    "services": [{"id": s["id"], "name": s.get("name")} for s in services],
                    "volume_gb": round(volume_mb / 1024, 3),
                },
            )

    def price(self, resources: list[Resource]) -> None:
        table = load_pricing(self.id)
        compute, default = table["compute"], table["default_service"]
        for r in resources:
            services = r.details.get("services") or []
            vcpu = len(services) * float(default["vcpu"])
            memory = len(services) * float(default["memory_gb"])
            volume_gb = float(r.details.get("volume_gb") or 0)
            r.details.update(vcpu=vcpu, memory_gb=memory)
            compute_usd = vcpu * compute["cpu_per_vcpu_month"] + memory * compute["memory_per_gb_month"]
            storage_usd = volume_gb * table["volume_per_gb_month"]
            r.monthly_usd = round(compute_usd + storage_usd, 2)
            r.plan = f"{len(services)} service(s)" + (f" + {volume_gb:g} GB volume" if volume_gb else "")
            r.pricing = (f"{len(services)} service(s) at the assumed {default['vcpu']:g} vCPU / "
                         f"{default['memory_gb']:g} GB each, always on; usage is metered per second so a mostly "
                         f"idle service costs less than this list price")

    def usage_cost(self, resources, usage, account, use):
        """Railway meters actual usage per second. Memory stays allocated while a service runs, so it is
        billed for the whole month; CPU is billed in proportion to how long the app is busy. Outbound
        transfer and volume storage are billed per GB."""
        table = load_pricing(self.id)
        compute = table["compute"]
        awake = min(usage.awake_hours, HOURS_PER_MONTH) / HOURS_PER_MONTH
        total = 0.0
        for r in resources:
            vcpu = float(r.details.get("vcpu") or 0)
            memory = float(r.details.get("memory_gb") or 0)
            volume_gb = float(r.details.get("volume_gb") or 0)
            total += memory * compute["memory_per_gb_month"]  # memory allocated all month
            total += vcpu * compute["cpu_per_vcpu_month"] * awake  # CPU billed with activity
            total += volume_gb * table["volume_per_gb_month"]
        total += usage.transfer_gb * table["egress_per_gb"]
        return fixed_cost([], f"memory billed all month, CPU for ~{usage.awake_hours:g} h of activity, "
                          f"{usage.transfer_gb:.3g} GB egress at ${table['egress_per_gb']}/GB", extra=round(total, 2))

    def delete(self, resource: Resource) -> None:
        self.gql(PROJECT_DELETE, id=resource.id)
