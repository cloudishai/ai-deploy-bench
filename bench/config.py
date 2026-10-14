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
    # False for credentials agents must obtain themselves (Cloudish keys): never passed to them.
    provided: bool = True


@dataclasses.dataclass(frozen=True)
class Cloud:
    id: str
    name: str
    url: str
    credentials: tuple[Credential, ...]
    prerequisites: tuple[str, ...] = ()
    when_paid: tuple[str, ...] = ()

    @property
    def provided_credentials(self) -> tuple[Credential, ...]:
        return tuple(c for c in self.credentials if c.provided)


# An organization with the HIPAA configuration rejects Claude Code's advisor tool and pre-release API
# features (context management), so they're turned off for models that use such a key.
HIPAA_ENV = {"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1", "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"}


@dataclasses.dataclass(frozen=True)
class Model:
    id: str
    name: str
    model: str
    effort: str | None = None
    hipaa: bool = False

    @property
    def env(self) -> dict[str, str]:
        return dict(HIPAA_ENV) if self.hipaa else {}

    @property
    def label(self) -> str:
        """For reports, e.g. "Opus 5.5 · medium effort · HIPAA organization"."""
        parts = [self.name] + ([f"{self.effort} effort"] if self.effort else [])
        return " · ".join(parts + (["HIPAA organization"] if self.hipaa else []))


@dataclasses.dataclass(frozen=True)
class App:
    id: str
    name: str
    short: str = ""
    use: str = ""  # who runs it: "commercial" (a business) or "personal" (a person or club)

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
class Usage:
    """A month of traffic to price a deployment for. The function figures only matter where compute is
    billed per request (Vercel Functions); elsewhere what counts is how long the app is awake."""

    id: str
    label: str
    description: str
    awake_hours: float  # hours a scale-to-zero app runs, idle timeouts included
    requests: int
    function_share: float  # share of requests that reach app code instead of static files on a CDN
    function_cpu_ms: float  # CPU time per function invocation
    function_duration_ms: float  # wall-clock time per invocation, for provisioned memory
    function_memory_gb: float
    kb_per_request: float  # average response size, for outbound transfer

    @property
    def transfer_gb(self) -> float:
        return self.requests * self.kb_per_request / 1_000_000

    @property
    def function_invocations(self) -> float:
        return self.requests * self.function_share

    @property
    def function_cpu_hours(self) -> float:
        return self.function_invocations * self.function_cpu_ms / 3_600_000

    @property
    def function_memory_gb_hours(self) -> float:
        return self.function_invocations * self.function_duration_ms / 3_600_000 * self.function_memory_gb


@dataclasses.dataclass(frozen=True)
class Config:
    agent: dict[str, Any]
    defaults: dict[str, Any]
    models: tuple[Model, ...]
    clouds: tuple[Cloud, ...]
    apps: tuple[App, ...]
    model_prices: dict[str, dict[str, float]]
    human_steps: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    reviewer: dict[str, Any] = dataclasses.field(default_factory=dict)
    security_rubric: tuple[dict[str, Any], ...] = ()
    stack_rubric: tuple[dict[str, Any], ...] = ()
    version: int = 1
    hosting_usage: tuple[Usage, ...] = ()

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
                prerequisites=tuple(c.get("prerequisites") or ()),
                when_paid=tuple(c.get("when_paid") or ()),
            )
            for c in raw["clouds"]
        ),
        apps=tuple(App(**a) for a in raw["apps"]),
        model_prices=raw.get("model_prices", {}),
        human_steps=raw.get("human_steps", {}),
        reviewer=raw.get("reviewer", {}),
        security_rubric=tuple(raw.get("security_rubric") or ()),
        stack_rubric=tuple(raw.get("stack_rubric") or ()),
        version=int(raw.get("version") or 1),
        hosting_usage=tuple(Usage(id=key, **value) for key, value in (raw.get("hosting_usage") or {}).items()),
    )
