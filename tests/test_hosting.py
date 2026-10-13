"""Hosting cost at each traffic level in benchmark.yaml: scale-to-zero, allowances and plan terms."""

import pytest

from bench import config
from bench.clouds import ADAPTERS, base
from bench.clouds.base import Resource

USAGE = {u.id: u for u in config.load().hosting_usage}


def cost(cloud, resources, usage, use="personal", account=None):
    return ADAPTERS[cloud]({}).usage_cost(resources, USAGE[usage], account or {}, use)


def test_the_traffic_levels_follow_from_requests():
    light, busy = USAGE["light"], USAGE["busy"]
    assert busy.requests == 730 * 3600  # one a second
    assert busy.transfer_gb == pytest.approx(52.56)
    assert busy.function_cpu_hours == pytest.approx(7.3)
    assert light.awake_hours < busy.awake_hours == 730


def test_cloudish_costs_its_hourly_rate_while_awake():
    project = Resource("project", "a/web", "adb-x-web", monthly_usd=21.66, details={"hourly_usd": 21.66 / 730})
    assert cost("cloudish", [project], "light")["usd"] == pytest.approx(0.30)
    assert cost("cloudish", [project], "busy")["usd"] == pytest.approx(21.66)


def test_digitalocean_bills_transfer_beyond_the_pooled_allowance():
    app = Resource("app", "1", "adb-x", monthly_usd=5.0, details={"bandwidth_gib": 1})
    assert cost("digitalocean", [app], "light")["usd"] == 5.0
    busy = cost("digitalocean", [app], "busy")
    assert busy["usd"] == pytest.approx(5 + (52.56 / 1.073741824 - 1) * 0.02, abs=0.01) and "GiB billed" in busy["basis"]


def test_render_bills_transfer_beyond_the_hobby_workspace_allowance():
    free = Resource("service", "srv-1", "adb-x-web", plan="free", monthly_usd=0.0)
    assert cost("render", [free], "light")["usd"] == 0
    busy = cost("render", [free], "busy")
    assert busy["usd"] == pytest.approx((52.56 - 5) * 0.15, abs=0.01)
    assert "730 h of 750 free hours" in busy["basis"]


@pytest.mark.parametrize("use, usage, expected, why", [
    ("personal", "light", 0.0, "within Hobby"),
    ("personal", "busy", 20.0, "exceeds Hobby's limits (CDN requests"),
    ("commercial", "light", 20.0, "non-commercial use only"),
])
def test_vercel_prices_what_hobby_cannot_host_on_pro(use, usage, expected, why):
    project = Resource("project", "prj", "adb-x-web", monthly_usd=0.0, details={"team_id": "team_1"})
    result = cost("vercel", [project], usage, use=use, account={"team_plans": {"team_1": "hobby"}})
    assert result["usd"] == pytest.approx(expected) and why in result["basis"]


def test_vercel_pro_teams_pay_only_usage_beyond_the_credit():
    project = Resource("project", "prj", "adb-x-web", monthly_usd=0.0, details={"team_id": "team_1"})
    assert cost("vercel", [project], "busy", use="commercial", account={"team_plans": {"team_1": "pro"}})["usd"] == 0


def test_inventory_prices_every_traffic_level_and_flags_unpriced_resources():
    class Fixed(base.Cloud):
        id = "fixed"

        def list_resources(self):
            return [Resource("app", "1", "adb-x-web", monthly_usd=5.0), Resource("db", "2", "adb-x-db")]

    report = base.inventory(Fixed({}), "adb-x", [], None, usages=USAGE.values(), use="commercial")
    assert set(report["usage"]) == {"light", "busy"}
    assert report["usage"]["busy"] == {"usd": 5.0, "incomplete": True,
                                       "basis": "fixed monthly prices; traffic within the included allowances"}
