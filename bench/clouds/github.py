"""Scratch GitHub repositories and GHCR images an agent creates with the optional GH_TOKEN.

Some clouds only deploy from a Git repository or a container registry, so cells may get a token
for a dedicated GitHub account or organization (GH_OWNER). These resources are free but are
cleaned up like any other. Both the owner and the token's own user are scanned, because
`gh repo create <name>` without an owner creates the repository under the user.
"""

from __future__ import annotations

from typing import Any, Iterator
from urllib.parse import quote

from bench.clouds.base import Cloud, Resource, api_for

API = "https://api.github.com"


class GitHub(Cloud):
    id = "github"
    credentials = ("GH_TOKEN", "GH_OWNER")
    delete_order = ("package", "repository")

    def __init__(self, env) -> None:
        super().__init__(env)
        self.owner = env.get("GH_OWNER", "")
        self.api = api_for(API, env.get("GH_TOKEN", ""), **{"X-GitHub-Api-Version": "2022-11-28"})
        self._scopes: list[tuple[str, str]] | None = None

    def scopes(self) -> list[tuple[str, str]]:
        """(kind, login) pairs to scan: the owner (org or user) and the token's own user."""
        if self._scopes is None:
            user = (self.api.get("/user") or {}).get("login", "")
            owner_type = (self.api.get(f"/users/{self.owner}") or {}).get("type")
            scopes = [("org", self.owner)] if owner_type == "Organization" else []
            self._scopes = scopes + [("user", user)] if user else scopes
        return self._scopes

    def _pages(self, path: str, **params: Any) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            batch = self.api.get(path, per_page=100, page=page, **params) or []
            yield from batch
            if len(batch) < 100:
                return
            page += 1

    def list_resources(self) -> list[Resource]:
        try:
            scopes = self.scopes()
        except Exception as error:
            self.errors.append(f"listing GitHub scopes failed: {error}")
            return []
        found: dict[tuple[str, str], Resource] = {}
        for kind, login in scopes:
            for resource in (self.collect("repositories", lambda: self._repositories(kind, login))
                             + self.collect("packages", lambda: self._packages(kind, login))):
                found.setdefault((resource.kind, resource.id), resource)
        return list(found.values())

    def _repositories(self, kind: str, login: str) -> Iterator[Resource]:
        path = f"/orgs/{login}/repos" if kind == "org" else "/user/repos"
        for repo in self._pages(path, **({} if kind == "org" else {"affiliation": "owner"})):
            yield Resource(kind="repository", id=repo["full_name"], name=repo["name"],
                           created_at=repo.get("created_at"), url=repo.get("html_url"),
                           details={"private": repo.get("private"), "scope": kind, "login": login})

    def _packages(self, kind: str, login: str) -> Iterator[Resource]:
        path = f"/orgs/{login}/packages" if kind == "org" else "/user/packages"
        for package in self._pages(path, package_type="container"):
            yield Resource(kind="package", id=f"{login}/{package['name']}", name=package["name"],
                           created_at=package.get("created_at"),
                           details={"visibility": package.get("visibility"), "scope": kind, "login": login})

    def price(self, resources: list[Resource]) -> None:
        for r in resources:
            r.monthly_usd, r.pricing = 0.0, "free scratch resource"

    def delete(self, resource: Resource) -> None:
        if resource.kind == "repository":
            self.api.delete(f"/repos/{resource.id}")
            return
        # Container names may contain slashes, which the API expects percent-encoded.
        name = quote(resource.name, safe="")
        if resource.details.get("scope") == "org":
            self.api.delete(f"/orgs/{resource.details['login']}/packages/container/{name}")
        else:
            self.api.delete(f"/user/packages/container/{name}")
