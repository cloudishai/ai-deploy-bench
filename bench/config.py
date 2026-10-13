"""Loads benchmark.yaml and the app task files into typed objects."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Iterable, TypeVar

import yaml

ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = ROOT / "apps"


@dataclasses.dataclass(frozen=True)
class Credential:
    env: str
    description: str
    # Optional variables (account scoping) are passed and mentioned only when they are set.
    optional: bool = False


@dataclasses.dataclass(frozen=True)
class Cloud:
    id: str
    name: str
    url: str
    credentials: tuple[Credential, ...]


@dataclasses.dataclass(frozen=True)
class Model:
    id: str
    name: str
    model: str
    effort: str | None = None


@dataclasses.dataclass(frozen=True)
class App:
    id: str
    name: str
    short: str = ""

    @property
    def dir(self) -> Path:
        return APPS_DIR / self.id

    @property
    def task(self) -> str:
        return (self.dir / "TASK.md").read_text()

    @property
    def deploy_notes(self) -> str:
        path = self.dir / "DEPLOY.md"
        return path.read_text().strip() if path.exists() else ""

    @property
    def fixtures(self) -> Path | None:
        path = self.dir / "fixtures"
        return path if path.is_dir() else None


@dataclasses.dataclass(frozen=True)
class Config:
    agent: dict[str, Any]
    defaults: dict[str, Any]
    models: tuple[Model, ...]
    clouds: tuple[Cloud, ...]
    apps: tuple[App, ...]
    model_prices: dict[str, dict[str, float]]

    def cloud(self, cloud_id: str) -> Cloud:
        return _by_id(self.clouds, cloud_id, "cloud")

    def model(self, model_id: str) -> Model:
        return _by_id(self.models, model_id, "model")

    def app(self, app_id: str) -> App:
        return _by_id(self.apps, app_id, "app")

    def credential_names(self) -> set[str]:
        return {c.env for cloud in self.clouds for c in cloud.credentials}


T = TypeVar("T", Cloud, Model, App)


def _by_id(items: Iterable[T], item_id: str, kind: str) -> T:
    for item in items:
        if item.id == item_id:
            return item
    known = ", ".join(i.id for i in items)
    raise KeyError(f"unknown {kind} {item_id!r} (known: {known})")


def select(items: Iterable[T], spec: str | None, kind: str) -> list[T]:
    """Resolves 'all' or a comma-separated list of ids, keeping the requested order."""
    items = list(items)
    if not spec or spec.strip().lower() == "all":
        return items
    return [_by_id(items, part.strip(), kind) for part in spec.split(",") if part.strip()]


def load(path: Path = ROOT / "benchmark.yaml") -> Config:
    raw = yaml.safe_load(path.read_text())
    return Config(
        agent=raw.get("agent", {}),
        defaults=raw.get("defaults", {}),
        models=tuple(Model(**m) for m in raw["models"]),
        clouds=tuple(
            Cloud(
                id=c["id"],
                name=c["name"],
                url=c["url"],
                credentials=tuple(Credential(**cred) for cred in c.get("credentials", [])),
            )
            for c in raw["clouds"]
        ),
        apps=tuple(App(**a) for a in raw["apps"]),
        model_prices=raw.get("model_prices", {}),
    )
