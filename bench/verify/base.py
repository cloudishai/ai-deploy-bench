"""Shared plumbing for the per-app verifiers: HTTP helpers, check bookkeeping and scoring.

A verifier only talks to the deployed app through its public URL, so it works the same no matter
which stack or cloud the agent picked.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import json
import secrets
import statistics
import threading
import time
from typing import Any, Awaitable, Callable, Iterator
from urllib.parse import urlsplit

import httpx

from bench.verify.htmlscan import PageScan

USER_AGENT = "ai-deploy-bench-verifier/1.0"


class CheckFailed(Exception):
    """Raised inside a check block to fail it with a readable reason."""


@dataclasses.dataclass
class Check:
    id: str
    description: str
    required: bool = True
    status: str = "pending"  # passed | failed | skipped
    detail: str = ""
    duration_ms: int = 0

    def skip(self, reason: str) -> None:
        self.status = "skipped"
        self.detail = reason
        raise _Skipped()


class _Skipped(Exception):
    pass


def snippet(text: str, limit: int = 200) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def describe(error: BaseException) -> str:
    if isinstance(error, (CheckFailed, AssertionError)) and str(error):
        return str(error)
    if isinstance(error, httpx.TimeoutException):
        return f"request timed out ({type(error).__name__})"
    if isinstance(error, httpx.HTTPError):
        return f"request failed: {type(error).__name__}: {error}"
    return f"{type(error).__name__}: {error}"


def expect_status(response: httpx.Response, *codes: int) -> None:
    if response.status_code not in codes:
        expected = " or ".join(str(c) for c in codes)
        raise CheckFailed(
            f"{response.request.method} {response.request.url.path} returned {response.status_code}, "
            f"expected {expected}: {snippet(response.text)}"
        )


def expect_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        raise CheckFailed(
            f"{response.request.method} {response.request.url.path} did not return JSON: {snippet(response.text)}"
        ) from None


def expect_html(response: httpx.Response) -> None:
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        raise CheckFailed(f"{response.request.url.path} has Content-Type {content_type!r}, expected text/html")


def expect(condition: Any, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


def token(prefix: str = "") -> str:
    return prefix + secrets.token_hex(4)


class Verifier:
    """Base class. Subclasses set `app_id`/`ready_path` and implement `run()` with check blocks."""

    app_id = ""
    ready_path = "/"

    def __init__(
        self,
        base_url: str,
        *,
        inputs: dict[str, Any] | None = None,
        deployment: dict[str, Any] | None = None,
        browser: Any = None,
        timeout: float = 30.0,
        ready_timeout: float = 600.0,
        min_persistence_delay: float = 60.0,
        require_https: bool = True,
        browser_required: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.inputs = inputs or {}
        self.deployment = deployment or {}
        self.browser = browser
        self.ready_timeout = ready_timeout
        self.min_persistence_delay = min_persistence_delay
        self.require_https = require_https
        self.browser_required = browser_required
        self.deadline: float | None = None
        self.http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        self.checks: list[Check] = []
        self.started_at = time.monotonic()

    # -- check bookkeeping ---------------------------------------------------------------------

    @contextlib.contextmanager
    def check(self, check_id: str, description: str, required: bool = True) -> Iterator[Check]:
        check = Check(check_id, description, required)
        self.checks.append(check)
        start = time.monotonic()
        try:
            yield check
            check.status = "passed"
        except _Skipped:
            pass
        except Exception as error:  # every failure mode of a check is reported, never raised
            check.status = "failed"
            check.detail = describe(error)
        finally:
            check.duration_ms = int((time.monotonic() - start) * 1000)

    def passed(self, check_id: str) -> bool:
        return any(c.id == check_id and c.status == "passed" for c in self.checks)

    @staticmethod
    def depends_on(value: Any, what: str) -> Any:
        if value is None:
            raise CheckFailed(f"not run: depends on {what}")
        return value

    # -- HTTP ----------------------------------------------------------------------------------

    def require_browser(self, check: Check) -> None:
        """Skips a browser check when no browser is expected; fails it when one should have run."""
        if self.browser:
            return
        if self.browser_required:
            raise CheckFailed("browser unavailable: Playwright failed to launch")
        check.skip("browser unavailable")

    def _budget(self) -> None:
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise CheckFailed("not run: verification time budget exhausted")

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        self._budget()
        return self.http.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        self._budget()
        return self.http.post(path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        self._budget()
        return self.http.patch(path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        self._budget()
        return self.http.delete(path, **kwargs)

    def page(self, path: str, response: httpx.Response | None = None) -> PageScan:
        """Scans a page's HTML; falls back to the browser-rendered DOM for client-rendered pages."""
        response = response or self.get(path)
        scan = PageScan.parse(response.text)
        if scan.looks_client_rendered() and self.browser:
            rendered = self.browser.rendered_html(self.base_url + path)
            if rendered:
                scan = PageScan.parse(rendered)
        return scan

    def wait_ready(self) -> dict[str, Any]:
        """Polls `ready_path` until it returns 2xx, to absorb cold starts and in-flight rollouts."""
        start = time.monotonic()
        attempts, last = 0, ""
        first_response_ms = None
        while True:
            attempts += 1
            request_start = time.monotonic()
            try:
                response = self.http.get(self.ready_path, timeout=90.0)
                if first_response_ms is None:
                    first_response_ms = int((time.monotonic() - request_start) * 1000)
                last = f"HTTP {response.status_code}"
                if 200 <= response.status_code < 300:
                    return {
                        "ready": True,
                        "seconds_to_ready": round(time.monotonic() - start, 1),
                        "attempts": attempts,
                        "first_response_ms": first_response_ms,
                    }
            except httpx.HTTPError as error:
                last = describe(error)
            if time.monotonic() - start > self.ready_timeout:
                return {
                    "ready": False,
                    "seconds_to_ready": None,
                    "attempts": attempts,
                    "first_response_ms": first_response_ms,
                    "last_error": last,
                }
            time.sleep(min(10.0, 2.0 + attempts))

    def sleep_until_persistence_window(self, since: float) -> None:
        remaining = self.min_persistence_delay - (time.monotonic() - since)
        if remaining > 0:
            time.sleep(remaining)

    def measure_latency(self, samples: int = 10) -> dict[str, Any]:
        timings = []
        for _ in range(samples):
            start = time.monotonic()
            try:
                response = self.http.get(self.ready_path)
                if response.status_code < 500:
                    timings.append((time.monotonic() - start) * 1000)
            except httpx.HTTPError:
                pass
        if not timings:
            return {"samples": 0}
        timings.sort()
        return {
            "samples": len(timings),
            "p50_ms": round(statistics.median(timings)),
            "p90_ms": round(timings[min(len(timings) - 1, int(len(timings) * 0.9))]),
        }

    # -- entry point ---------------------------------------------------------------------------

    def run(self) -> None:
        raise NotImplementedError

    @staticmethod
    def run_async(coroutine_factory: Callable[[], Awaitable[None]]) -> None:
        """Runs async checks on their own thread so their event loop can't clash with Playwright's."""
        errors: list[BaseException] = []

        def target() -> None:
            try:
                asyncio.run(coroutine_factory())
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=target, name="async-checks")
        thread.start()
        thread.join()
        if errors:
            raise errors[0]

    def run_all(self) -> dict[str, Any]:
        readiness = self.wait_ready()
        with self.check("ready", f"GET {self.ready_path} answers 2xx within {self.ready_timeout / 60:g} min"):
            expect(readiness["ready"], f"never answered 2xx (last: {readiness.get('last_error')})")
        # Bound the whole run so a hanging host can't outlast the workflow step; when the app never
        # answered, still try the checks for partial credit, but quickly.
        if readiness["ready"]:
            self.deadline = time.monotonic() + 15 * 60
        else:
            self.deadline = time.monotonic() + 3 * 60
            self.http.timeout = httpx.Timeout(5.0)
        with self.check("https", "The app is served over HTTPS with a valid certificate") as check:
            if not self.require_https:
                check.skip("HTTPS not required for this run")
            expect(urlsplit(self.base_url).scheme == "https", f"URL {self.base_url} is not https")
            self.get(self.ready_path)
        with self.check("public_access", "The app is public: no redirect to another host such as a login page"):
            response = self.get(self.ready_path)
            expected, final = _bare_host(urlsplit(self.base_url).hostname), _bare_host(response.url.host)
            expect(final == expected, f"{self.ready_path} redirected to {response.url}")
            expect(response.status_code not in (401, 403), f"{self.ready_path} returned {response.status_code}")
        try:
            self.run()
        except Exception as error:  # a verifier bug must not hide the checks that already ran
            self.checks.append(Check("verifier_error", "Verifier crashed before finishing", True, "failed", describe(error)))
        performance = self.measure_latency() if readiness["ready"] else {"samples": 0}
        self.http.close()
        return summarize(self.checks, readiness, performance)


def _bare_host(host: str | None) -> str:
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def summarize(checks: list[Check], readiness: dict[str, Any], performance: dict[str, Any]) -> dict[str, Any]:
    scored = [c for c in checks if c.status in ("passed", "failed")]
    passed = [c for c in scored if c.status == "passed"]
    required_failed = [c for c in checks if c.required and c.status == "failed"]
    return {
        "readiness": readiness,
        "performance": performance,
        "checks": [dataclasses.asdict(c) for c in checks],
        "passed": len(passed),
        "failed": len(scored) - len(passed),
        "skipped": len(checks) - len(scored),
        "score": round(len(passed) / len(scored), 4) if scored else 0.0,
        "required_failed": [c.id for c in required_failed],
        "success": bool(readiness.get("ready")) and not required_failed,
    }


def dump(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2)
