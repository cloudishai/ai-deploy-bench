"""Runs each verifier against a correct reference app and against deliberately broken ones."""

import pytest

from bench.verify import VERIFIERS
from bench.verify.browser import Browser
from tests.reference_apps import Server, api_app, crud_app, dataviz_app, realtime_app, static_app

KEYS = ["key-alpha", "key-beta"]


@pytest.fixture(scope="module")
def browser():
    instance = Browser.launch()
    yield instance
    if instance:
        instance.close()


def verify(app_id, app, browser=None, **kwargs):
    with Server(app) as url:
        verifier = VERIFIERS[app_id](
            url, require_https=False, min_persistence_delay=0, ready_timeout=10, browser=browser, **kwargs
        )
        return verifier.run_all()


def statuses(result):
    return {c["id"]: c["status"] for c in result["checks"]}


def failures(result):
    return {c["id"]: c["detail"] for c in result["checks"] if c["status"] == "failed"}


REFERENCE = {
    "static": lambda: (static_app(), {}),
    "crud": lambda: (crud_app(), {}),
    "api": lambda: (api_app(KEYS), {"inputs": {"api_keys": KEYS}}),
    "dataviz": lambda: (dataviz_app(), {}),
    "realtime": lambda: (realtime_app(), {}),
    "realtime-sse": lambda: (realtime_app(), {"deployment": {"realtime": {"transport": "sse"}}}),
}


@pytest.mark.parametrize("name", REFERENCE)
def test_reference_app_passes(name, browser):
    app, kwargs = REFERENCE[name]()
    result = verify(name.split("-")[0], app, browser, **kwargs)
    assert failures(result) == {}
    assert result["success"]
    assert result["readiness"]["ready"]
    if browser is None:
        assert all(s in ("passed", "skipped") for s in statuses(result).values())


def test_static_without_contact_api(browser):
    result = verify("static", static_app(frozenset({"no_contact_api"})), browser)
    assert {"contact_api_valid", "contact_api_validation"} <= failures(result).keys()
    assert not result["success"]


def test_static_without_validation():
    result = verify("static", static_app(frozenset({"no_validation"})))
    assert set(failures(result)) == {"contact_api_validation"}


def test_static_form_that_reloads_the_page(browser):
    if browser is None:
        pytest.skip("Playwright is not installed")
    result = verify("static", static_app(frozenset({"full_reload"})), browser)
    assert "browser_contact_form" in failures(result)


def test_static_client_rendered_pages_need_the_browser(browser):
    if browser is None:
        pytest.skip("Playwright is not installed")
    app = static_app(frozenset({"spa"}))
    assert verify("static", app, browser)["success"]
    without_browser = verify("static", static_app(frozenset({"spa"})))
    assert {"home_content", "about_content"} <= failures(without_browser).keys()


def test_browser_checks_run_when_available(browser):
    if browser is None:
        pytest.skip("Playwright is not installed")
    result = verify("dataviz", dataviz_app(), browser)
    assert {k: v for k, v in statuses(result).items() if k.startswith("browser_")} == {
        "browser_chart": "passed", "browser_two_charts": "passed", "browser_filters": "passed"}


def test_crud_without_isolation():
    result = verify("crud", crud_app(frozenset({"no_isolation"})))
    assert "isolation" in failures(result)
    assert not result["success"]


def test_api_without_rate_limit():
    result = verify("api", api_app(KEYS, frozenset({"no_rate_limit"})), inputs={"api_keys": KEYS})
    assert "rate_limit" in failures(result)


def test_api_with_global_rate_limit():
    result = verify("api", api_app(KEYS, frozenset({"global_rate_limit"})), inputs={"api_keys": KEYS})
    assert "rate_limit_per_key" in failures(result)


def test_dataviz_with_wrong_counts():
    result = verify("dataviz", dataviz_app(frozenset({"off_by_one"})))
    assert {"summary_all", "summary_region", "summary_category", "summary_combined"} <= failures(result).keys()


def test_realtime_without_broadcast():
    result = verify("realtime", realtime_app(frozenset({"no_broadcast"})))
    assert {"delivery", "fanout"} <= failures(result).keys()


def test_realtime_leaking_rooms():
    result = verify("realtime", realtime_app(frozenset({"leak_rooms"})))
    assert "room_isolation" in failures(result)


def test_unreachable_app_is_not_ready():
    verifier = VERIFIERS["static"]("http://127.0.0.1:9", require_https=False, ready_timeout=0.5)
    result = verifier.run_all()
    assert not result["readiness"]["ready"]
    assert not result["success"]


def test_required_browser_checks_fail_when_the_browser_is_missing():
    with Server(static_app()) as url:
        verifier = VERIFIERS["static"](url, require_https=False, ready_timeout=10, browser=None, browser_required=True)
        result = verifier.run_all()
    assert "browser unavailable" in failures(result)["browser_contact_form"]
    assert not result["success"]


def test_verifier_crash_is_never_a_success():
    class Crashing(VERIFIERS["static"]):
        def run(self):
            raise RuntimeError("bug in a verifier")

    with Server(static_app()) as url:
        result = Crashing(url, require_https=False, ready_timeout=10).run_all()
    assert "verifier_error" in result["required_failed"] and not result["success"]


def test_time_budget_stops_remaining_checks():
    class Slow(VERIFIERS["static"]):
        def run(self):
            self.deadline = 0  # already exhausted
            with self.check("late", "A check that starts after the budget"):
                self.get("/")

    with Server(static_app()) as url:
        result = Slow(url, require_https=False, ready_timeout=10).run_all()
    assert "time budget exhausted" in failures(result)["late"]
