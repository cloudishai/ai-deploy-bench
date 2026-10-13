"""Cloud adapters against mocked provider APIs: matching, pricing, leak detection and teardown."""

import httpx
import pytest

from bench.clouds import ADAPTERS, base
from bench.clouds.base import Cloud, Resource
from bench.clouds.github import GitHub
from bench.clouds.http import Api

PREFIX = "adb-k3x9f-crud"


class FakeApi:
    """Routes (method, host+path) to canned JSON and records every call."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        # The raw path keeps percent-encoding (url.path would decode %2F into /).
        key = (request.method, request.url.host + request.url.raw_path.split(b"?")[0].decode())
        self.calls.append((key, dict(request.url.params)))
        if key not in self.routes:
            return httpx.Response(404, json={"error": "not found"})
        body = self.routes[key]
        body = body(request) if callable(body) else body
        return httpx.Response(204) if body is None else httpx.Response(200, json=body)

    def deleted(self):
        return [path for (method, path), _ in self.calls if method == "DELETE"]


@pytest.fixture
def fake(monkeypatch):
    def install(routes):
        api = FakeApi(routes)
        monkeypatch.setattr(Api, "transport", httpx.MockTransport(api))
        monkeypatch.setattr(Api, "retry_sleep", 0)
        return api

    return install


def by_name(result):
    return {r["name"]: r for r in result["resources"]}


def test_cloudish_prices_live_and_deletes(fake):
    api = fake({
        ("GET", "cloudish.ai/api/v1/projects"): {"projects": [
            {"path": "bench/adb-k3x9f-crud", "name": "adb-k3x9f-crud", "owner": {"alias": "bench"}},
            {"path": "bench/unrelated", "name": "unrelated"},
        ]},
        ("GET", "cloudish.ai/api/v1/projects/bench/adb-k3x9f-crud"): {
            "project": {"name": "adb-k3x9f-crud"},
            "app": {"cpuCores": 0.5, "memoryGb": 1, "replicas": 1, "status": "running"},
            "subdomain": {"url": "https://abc.run.cloudish.ai/"},
        },
        ("GET", "cloudish.ai/api/v1/projects/bench/unrelated"): {"project": {}},
        ("GET", "cloudish.ai/api/v1/pricing"): base.load_pricing("cloudish")["pricing"],
        ("GET", "cloudish.ai/api/v1/credits"): {"balance": 4.2},
        ("DELETE", "cloudish.ai/api/v1/projects/bench/adb-k3x9f-crud"): {"ok": True},
    })
    cloud = ADAPTERS["cloudish"]({"CLOUDISH_API_KEY": "cld_test"})
    result = base.inventory(cloud, PREFIX, [], None)
    project = by_name(result)["adb-k3x9f-crud"]
    assert project["url"] == "https://abc.run.cloudish.ai/"
    assert project["plan"] == "small"
    assert project["monthly_usd"] == pytest.approx(21.66, abs=0.01)
    assert set(by_name(result)) == {"adb-k3x9f-crud"}
    assert result["account"] == {"balance_usd": 4.2}
    outcomes = base.teardown(cloud, result["resources"], retry_delay=0)
    assert outcomes == [{"kind": "project", "name": "adb-k3x9f-crud", "deleted": True}]
    assert api.deleted() == ["cloudish.ai/api/v1/projects/bench/adb-k3x9f-crud"]


def test_render_maps_legacy_and_new_plan_ids(fake):
    fake({
        ("GET", "api.render.com/v1/owners"): [{"owner": {"id": "tea-1"}, "cursor": "c1"}],
        ("GET", "api.render.com/v1/services"): [
            {"service": {"id": "srv-1", "name": "adb-k3x9f-crud-web", "type": "web_service", "createdAt": "2026-10-12T10:00:00Z",
                         "serviceDetails": {"plan": "0.5c-512mb", "numInstances": 1, "url": "https://adb.onrender.com"}}, "cursor": "a"},
            {"service": {"id": "srv-2", "name": "adb-k3x9f-crud-site", "type": "static_site",
                         "serviceDetails": {"url": "https://site.onrender.com"}}, "cursor": "b"},
        ],
        ("GET", "api.render.com/v1/postgres"): [
            {"postgres": {"id": "dpg-1", "name": "adb-k3x9f-crud-db", "plan": "basic_256mb", "diskSizeGB": 1}, "cursor": "p"},
        ],
        ("GET", "api.render.com/v1/key-value"): [],
        ("GET", "api.render.com/v1/env-groups"): [],
        ("GET", "api.render.com/v1/registrycredentials"): [],
        ("GET", "api.render.com/v1/projects"): [],
    })
    result = base.inventory(ADAPTERS["render"]({"RENDER_API_KEY": "rnd_test"}), PREFIX, [], None)
    resources = by_name(result)
    assert resources["adb-k3x9f-crud-web"]["monthly_usd"] == 7
    assert resources["adb-k3x9f-crud-site"]["monthly_usd"] == 0
    assert resources["adb-k3x9f-crud-db"]["monthly_usd"] == pytest.approx(6.30)
    assert result["monthly_usd"] == pytest.approx(13.30)
    assert not result["errors"]


def test_vercel_uses_production_alias_and_team_scope(fake):
    api = fake({
        ("GET", "api.vercel.com/v2/teams"): {"teams": [{"id": "team_1", "slug": "bench"}]},
        ("GET", "api.vercel.com/v10/projects"): {"projects": [
            {"id": "prj_1", "name": "adb-k3x9f-crud", "createdAt": 1760263200000,
             "targets": {"production": {"alias": ["adb-k3x9f-crud.vercel.app"], "url": "adb-k3x9f-crud-abc.vercel.app"}}},
        ], "pagination": {"next": None}},
        ("GET", "api.vercel.com/v1/storage/stores"): {"stores": [
            {"id": "store_1", "name": "adb-k3x9f-crud-db", "type": "integration",
             "billingPlan": {"type": "free", "name": "Free"}, "product": {"slug": "neon"}},
        ]},
        ("GET", "api.vercel.com/v1/global-config"): [],
        ("GET", "api.vercel.com/v2/teams/team_1"): {"billing": {"plan": "hobby"}},
        ("DELETE", "api.vercel.com/v9/projects/prj_1"): None,
        ("DELETE", "api.vercel.com/v1/storage/stores/store_1/connections"): None,
        ("DELETE", "api.vercel.com/v1/storage/stores/integration/store_1"): None,
    })
    cloud = ADAPTERS["vercel"]({"VERCEL_TOKEN": "vcp_test"})
    result = base.inventory(cloud, PREFIX, [], None)
    resources = by_name(result)
    assert resources["adb-k3x9f-crud"]["url"] == "https://adb-k3x9f-crud.vercel.app"
    assert resources["adb-k3x9f-crud-db"]["monthly_usd"] == 0
    assert result["account"] == {"team_plans": {"team_1": "hobby"}}
    # Both the team and the personal scope are scanned; the same project seen twice is listed once.
    project_scopes = [params.get("teamId") for (method, path), params in api.calls if path.endswith("/v10/projects")]
    assert project_scopes == ["team_1", None]
    assert [r["name"] for r in result["resources"]].count("adb-k3x9f-crud") == 1
    base.teardown(cloud, result["resources"], retry_delay=0)
    # Stores are disconnected and deleted before the project, in the team scope they were found in.
    assert api.deleted() == [
        "api.vercel.com/v1/storage/stores/store_1/connections",
        "api.vercel.com/v1/storage/stores/integration/store_1",
        "api.vercel.com/v9/projects/prj_1",
    ]
    assert all(params.get("teamId") == "team_1" for (method, _), params in api.calls if method == "DELETE")


DO_EMPTY = {
    ("GET", "api.digitalocean.com/v2/databases"): {"databases": []},
    ("GET", "api.digitalocean.com/v2/droplets"): {"droplets": []},
    ("GET", "api.digitalocean.com/v2/volumes"): {"volumes": []},
    ("GET", "api.digitalocean.com/v2/load_balancers"): {"load_balancers": []},
    ("GET", "api.digitalocean.com/v2/kubernetes/clusters"): {"kubernetes_clusters": []},
    ("GET", "api.digitalocean.com/v2/functions/namespaces"): {"namespaces": []},
    ("GET", "api.digitalocean.com/v2/registries"): {"registries": []},
    ("GET", "api.digitalocean.com/v2/spaces/keys"): {"keys": []},
    ("GET", "api.digitalocean.com/v2/projects"): {"projects": [{"id": "p0", "name": "default", "is_default": True}]},
}


def test_digitalocean_prices_app_components(fake):
    fake(DO_EMPTY | {
        ("GET", "api.digitalocean.com/v2/apps"): {"apps": [
            {"id": "a1", "created_at": "2026-10-12T10:00:00Z", "live_url": "https://adb-k3x9f-crud-x.ondigitalocean.app",
             "spec": {"name": "adb-k3x9f-crud", "services": [{"name": "web", "instance_size_slug": "apps-s-1vcpu-1gb", "instance_count": 2}],
                      "databases": [{"name": "db", "engine": "PG"}]}},
            {"id": "a2", "spec": {"name": "adb-k3x9f-crud-site", "static_sites": [{"name": "site"}]}},
        ], "links": {}},
        ("GET", "api.digitalocean.com/v2/apps/tiers/instance_sizes"): {"instance_sizes": [
            {"slug": "apps-s-1vcpu-1gb", "usd_per_month": "12.00"},
        ]},
    })
    result = base.inventory(ADAPTERS["digitalocean"]({"DIGITALOCEAN_ACCESS_TOKEN": "dop_v1_test"}), PREFIX, [], None)
    resources = by_name(result)
    assert resources["adb-k3x9f-crud"]["monthly_usd"] == 31  # 2 x $12 + $7 dev database
    assert resources["adb-k3x9f-crud"]["url"].endswith(".ondigitalocean.app")
    assert resources["adb-k3x9f-crud-site"]["monthly_usd"] == 0
    assert "default" not in resources


def test_unmatched_resources_created_during_the_cell_are_reported_not_deleted(fake):
    fake(DO_EMPTY | {
        ("GET", "api.digitalocean.com/v2/apps"): {"apps": [
            {"id": "a1", "created_at": "2026-10-12T10:05:00Z", "spec": {"name": "my-app"}},
            {"id": "a2", "created_at": "2026-10-01T00:00:00Z", "spec": {"name": "older-app"}},
            {"id": "a3", "created_at": "2026-10-12T10:06:00Z", "spec": {"name": "declared-app"}},
        ]},
    })
    declared = [{"name": "declared-app", "type": "app"}]
    result = base.inventory(ADAPTERS["digitalocean"]({"DIGITALOCEAN_ACCESS_TOKEN": "t"}), PREFIX, declared, "2026-10-12T10:00:00+00:00")
    assert [r["name"] for r in result["resources"]] == ["declared-app"]
    assert result["resources"][0]["matched_by"] == "declared"
    assert [r["name"] for r in result["possible_leaks"]] == ["my-app"]


def test_listing_failures_are_recorded_not_raised(fake):
    fake({("GET", "api.render.com/v1/owners"): [{"owner": {"id": "tea-1"}}]})
    result = base.inventory(ADAPTERS["render"]({"RENDER_API_KEY": "k"}), PREFIX, [], None)
    assert result["resources"] == []
    assert any("services" in e for e in result["errors"])


def test_teardown_retries_dependencies():
    class Flaky(Cloud):
        id, delete_order = "flaky", ("app", "database")
        attempts: dict = {}

        def delete(self, resource):
            self.attempts[resource.id] = self.attempts.get(resource.id, 0) + 1
            if resource.kind == "database" and self.attempts[resource.id] == 1:
                raise RuntimeError("still attached")

    cloud = Flaky({})
    resources = [Resource("database", "d1", "adb-db").to_dict(), Resource("app", "a1", "adb-app").to_dict()]
    outcomes = base.teardown(cloud, resources, retry_delay=0)
    assert all(o["deleted"] for o in outcomes)
    assert Flaky.attempts == {"a1": 1, "d1": 2}


def test_github_scratch_resources_in_the_org_and_the_tokens_user(fake):
    api = fake({
        ("GET", "api.github.com/user"): {"login": "bench-bot"},
        ("GET", "api.github.com/users/bench-org"): {"type": "Organization"},
        ("GET", "api.github.com/orgs/bench-org/repos"): [
            {"full_name": "bench-org/adb-k3x9f-crud", "name": "adb-k3x9f-crud"},
            {"full_name": "bench-org/keep-me", "name": "keep-me"},
        ],
        ("GET", "api.github.com/orgs/bench-org/packages"): [{"name": "adb-k3x9f-crud/web"}],
        # `gh repo create` without an owner puts the repository under the token's user.
        ("GET", "api.github.com/user/repos"): [{"full_name": "bench-bot/adb-k3x9f-crud-site", "name": "adb-k3x9f-crud-site"}],
        ("GET", "api.github.com/user/packages"): [],
        ("DELETE", "api.github.com/repos/bench-org/adb-k3x9f-crud"): None,
        ("DELETE", "api.github.com/repos/bench-bot/adb-k3x9f-crud-site"): None,
        ("DELETE", "api.github.com/orgs/bench-org/packages/container/adb-k3x9f-crud%2Fweb"): None,
    })
    cloud = GitHub({"GH_TOKEN": "ghp_test", "GH_OWNER": "bench-org"})
    result = base.inventory(cloud, PREFIX, [], None)
    assert sorted(by_name(result)) == ["adb-k3x9f-crud", "adb-k3x9f-crud-site", "adb-k3x9f-crud/web"]
    outcomes = base.teardown(cloud, result["resources"], retry_delay=0)
    assert all(o["deleted"] for o in outcomes)
    assert sorted(api.deleted()) == [
        "api.github.com/orgs/bench-org/packages/container/adb-k3x9f-crud%2Fweb",
        "api.github.com/repos/bench-bot/adb-k3x9f-crud-site",
        "api.github.com/repos/bench-org/adb-k3x9f-crud",
    ]


def test_digitalocean_sends_a_json_content_type_on_deletes(fake):
    seen = []

    def delete_project(request):
        seen.append(request.headers.get("content-type"))
        return None

    fake({("DELETE", "api.digitalocean.com/v2/projects/p1"): delete_project})
    cloud = ADAPTERS["digitalocean"]({"DIGITALOCEAN_ACCESS_TOKEN": "t"})
    outcomes = base.teardown(cloud, [Resource("project", "p1", "adb-k3x9f-crud").to_dict()], retry_delay=0)
    assert outcomes[0]["deleted"] and seen == ["application/json"]
