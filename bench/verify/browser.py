"""Optional headless Chromium (Playwright) for checks that need a real browser.

Browser checks are skipped, not failed, when Playwright isn't installed, so the HTTP checks can
run anywhere. The benchmark workflow always installs it.
"""

from __future__ import annotations

import contextlib
from typing import Any, Iterator


class Browser:
    def __init__(self, playwright: Any, chromium: Any) -> None:
        self._playwright = playwright
        self._chromium = chromium

    @classmethod
    def launch(cls) -> "Browser | None":
        try:
            from playwright.sync_api import sync_playwright

            playwright = sync_playwright().start()
        except Exception:  # not installed, or the driver failed to start
            return None
        try:
            return cls(playwright, playwright.chromium.launch())
        except Exception:  # browser binaries missing
            playwright.stop()
            return None

    @contextlib.contextmanager
    def page(self, viewport: dict[str, int] | None = None) -> Iterator[tuple[Any, list[str]]]:
        """Yields a fresh page and a list that collects uncaught page errors."""
        context = self._chromium.new_context(viewport=viewport or {"width": 1280, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            yield page, errors
        finally:
            context.close()

    def rendered_html(self, url: str) -> str:
        try:
            with self.page() as (page, _):
                page.goto(url, wait_until="networkidle")
                return page.content()
        except Exception:
            return ""

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._chromium.close()
        with contextlib.suppress(Exception):
            self._playwright.stop()
