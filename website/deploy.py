"""Deploys the built site to Cloudish: python -m website.deploy [--dist website/dist]. Needs CLOUDISH_API_KEY.

Uploads website/Dockerfile, website/nginx.conf and dist/ as a build context, waits for Cloudish to
build and run the image, keeps the project's subdomain and custom domains configured, then checks
that the new build is the one being served. Safe to run on every push: every step is idempotent.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tarfile
import time
from pathlib import Path
from typing import Any, Callable

import httpx

HERE = Path(__file__).resolve().parent
API = "https://cloudish.ai/api/v1"
PROJECT = "aideploybench"  # also the subdomain label: https://aideploybench.<run domain>/
DOMAINS = (("aideploybench.com", False), ("www.aideploybench.com", True))  # (host, redirects to the first)
DNS_TARGET = "do.cloudish.ai"
BUILD_TIMEOUT_S = 900
LIVE_TIMEOUT_S = 300
BUILD_META = re.compile(r'<meta name="build" content="([^"]*)">')


class DeployError(Exception):
    pass


def build_context(dist: Path) -> bytes:
    """A tar.gz build context: the Dockerfile at its root, nginx.conf and dist/."""
    if not (dist / "index.html").is_file():
        raise DeployError(f"{dist} has no index.html; run python -m website.build first")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        tar.add(HERE / "Dockerfile", arcname="Dockerfile")
        tar.add(HERE / "nginx.conf", arcname="nginx.conf")
        tar.add(dist, arcname="dist")
    return buffer.getvalue()


def built_sha(dist: Path) -> str:
    match = BUILD_META.search((dist / "index.html").read_text())
    return match.group(1) if match else ""


class Cloudish:
    def __init__(self, key: str, transport: httpx.BaseTransport | None = None) -> None:
        self.http = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {key}"}, timeout=180,
                                 transport=transport)

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.http.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise DeployError(f"{method} {path} -> HTTP {response.status_code}: {response.text[:800]}")
        return response.json() if response.content else {}


def deploy(api: Cloudish, dist: Path, project: str = PROJECT, domains=DOMAINS, site: httpx.Client | None = None,
           log: Callable[[str], None] = print, sleep: Callable[[float], None] = time.sleep) -> str:
    """Deploys `dist` and returns the URL it's served at."""
    me = api.call("GET", "/me")
    owner = (me.get("apiKey") or me)["alias"]
    log(f"deploying {dist} as {owner}/{project}")
    # "open": anyone with the link can visit, and it isn't listed in Cloudish's gallery.
    created = api.call("POST", "/projects", data={"name": project, "port": "8080", "access": "open"},
                       files={"context": ("context.tar.gz", build_context(dist), "application/gzip")})
    build_id = created["build"]["id"]
    shown, deadline = "", time.monotonic() + BUILD_TIMEOUT_S
    while True:
        status = api.call("GET", f"/images/builds/{build_id}")
        build = status.get("build") or {}
        logs = build.get("logs") or ""
        # The log is the build's tail: print what's new since the last poll.
        for line in (logs[len(shown):] if logs.startswith(shown) else logs).splitlines():
            log(f"  build: {line}")
        shown = logs
        if build.get("status") == "succeeded":
            break
        if build.get("status") in ("failed", "cancelled"):
            raise DeployError(f"build {build_id} {build.get('status')}: {build.get('error') or 'see the log above'}")
        if time.monotonic() > deadline:
            raise DeployError(f"build {build_id} still {build.get('status')} after {BUILD_TIMEOUT_S}s")
        sleep(5)
    log(f"build {build_id} succeeded")

    path = f"/projects/{owner}/{project}"
    url = ((api.call("GET", path).get("subdomain") or {}).get("url") or "").rstrip("/")
    if not url.startswith(f"https://{project}."):
        url = (api.call("PUT", f"{path}/subdomain", json={"label": project})["subdomain"]["url"]).rstrip("/")
    log(f"subdomain: {url}/")

    existing = {d["host"]: d for d in api.call("GET", f"{path}/domains").get("domains") or []}
    for host, redirect in domains:
        domain = existing.get(host)
        if domain is None:
            domain = api.call("POST", f"{path}/domains", json={"host": host, "redirect": redirect})["domain"]
        elif bool(domain.get("redirect")) != redirect:
            domain = api.call("PATCH", f"{path}/domains/{host}", json={"redirect": redirect}).get("domain", domain)
        log(f"domain {host}: {domain.get('status')}" + (" (redirects)" if redirect else ""))
        if domain.get("status") != "active":
            txt = domain.get("txtRecord") or {}
            if txt:
                log(f"  DNS: TXT {txt.get('name')} = {txt.get('value')}")
            pointer = "CNAME" if host.count(".") > 1 else "A (or ALIAS/flattened CNAME)"
            log(f"  DNS: {pointer} {host} -> {DNS_TARGET}")

    expected = built_sha(dist)
    client = site or httpx.Client(timeout=30, follow_redirects=True)
    deadline = time.monotonic() + LIVE_TIMEOUT_S
    while True:
        try:
            response = client.get(f"{url}/")
            served = BUILD_META.search(response.text)
            if response.status_code == 200 and served and served.group(1) == expected:
                break
            seen = f"HTTP {response.status_code}, build {served.group(1)[:7] if served else 'unknown'}"
        except httpx.HTTPError as error:
            seen = f"{type(error).__name__}"
        if time.monotonic() > deadline:
            raise DeployError(f"{url}/ didn't serve build {expected[:7]} within {LIVE_TIMEOUT_S}s (last: {seen})")
        sleep(5)
    log(f"live: {url}/ serves build {expected[:7]}")
    return url


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m website.deploy", description=__doc__)
    parser.add_argument("--dist", type=Path, default=HERE / "dist")
    parser.add_argument("--project", default=PROJECT)
    args = parser.parse_args(argv)
    key = os.environ.get("CLOUDISH_API_KEY")
    if not key:
        sys.exit("CLOUDISH_API_KEY is not set")
    try:
        deploy(Cloudish(key), args.dist, args.project)
    except DeployError as error:
        sys.exit(f"deploy failed: {error}")


if __name__ == "__main__":
    main()
