"""A small JSON-over-HTTPS client with retries, shared by the cloud adapters."""

from __future__ import annotations

import time
from typing import Any

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}


class ApiError(Exception):
    def __init__(self, method: str, url: str, status: int, body: str) -> None:
        super().__init__(f"{method} {url} -> HTTP {status}: {body[:300]}")
        self.status = status


class Api:
    # Tests swap in an httpx.MockTransport here.
    transport: httpx.BaseTransport | None = None
    retry_sleep: float = 1.0

    def __init__(self, base_url: str, headers: dict[str, str], timeout: float = 30.0) -> None:
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Accept": "application/json", "User-Agent": "ai-deploy-bench/1.0", **headers},
            timeout=timeout,
            transport=Api.transport,
        )

    def request(self, method: str, path: str, *, ok_missing: bool = False, **kwargs: Any) -> Any:
        """Sends a request, retrying throttling and server errors. Returns parsed JSON or None."""
        for attempt in range(5):
            try:
                response = self.client.request(method, path, **kwargs)
            except httpx.TransportError:
                if attempt == 4:
                    raise
                time.sleep(self.retry_sleep * 2 ** attempt)
                continue
            if response.status_code in RETRY_STATUS and attempt < 4:
                time.sleep(self.retry_sleep * _retry_after(response, 2 ** attempt))
                continue
            if ok_missing and response.status_code == 404:
                return None
            if response.status_code >= 400:
                raise ApiError(method, str(response.request.url), response.status_code, response.text)
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return response.text
        return None

    def get(self, path: str, **params: Any) -> Any:
        return self.request("GET", path, params={k: v for k, v in params.items() if v is not None})

    def delete(self, path: str, **kwargs: Any) -> None:
        """Deletes a resource; one that is already gone counts as deleted."""
        self.request("DELETE", path, ok_missing=True, **kwargs)

    def close(self) -> None:
        self.client.close()


def _retry_after(response: httpx.Response, default: float) -> float:
    try:
        return min(60.0, max(1.0, float(response.headers.get("retry-after", default))))
    except ValueError:
        return default
