"""Reads results/ into runs and cells, and the metrics the site charts.

Runs written by older versions of the benchmark have older schemas, so every field added after
schema 1 is optional here (see "Result files" in docs/methodology.md).
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import statistics
from pathlib import Path
from typing import Any, Callable

from bench import config, fmt, stack

FULL = "full"


@dataclasses.dataclass
class Cell:
    run: "Run"
    summary: dict[str, Any]  # the cell's row in summary.json
    record: dict[str, Any] | None  # its full record, when one was committed
    report: str  # its markdown report, or ""
    source: Path  # results/runs/<run>/cells/<model>/<cloud>/<app>-t<trial>, without a suffix

    def __getattr__(self, name: str) -> Any:
        """Fields of the summary row; None when an older schema doesn't have them."""
        if name.startswith("__"):
            raise AttributeError(name)
        return self.__dict__.get("summary", {}).get(name)

    @property
    def slug(self) -> str:
        return f"{self.model}/{self.cloud}/{self.app}-t{self.trial}"

    @property
    def href(self) -> str:
        return f"{self.run.href}{self.slug}/"

    @property
    def results_path(self) -> str:
        """The record's path in the repository."""
        return f"results/runs/{self.run.name}/cells/{self.slug}"

    @property
    def screenshots(self) -> list[dict[str, Any]]:
        """Screenshots with a file on disk (`path`), in the order the verifier took them."""
        shots = []
        for shot in (self.record or {}).get("screenshots") or []:
            if shot.get("file") and (self.source.parent / shot["file"]).is_file():
                shots.append({**shot, "path": self.source.parent / shot["file"], "name": Path(shot["file"]).name})
        return shots

    @property
    def technologies(self) -> dict[str, list[str]]:
        """By group, named from the record's facts (bench/stack.py), so older runs benefit from a
        better catalog too."""
        return stack.describe(self.record) if self.record else {}

    @property
    def stack_headline(self) -> list[str]:
        return stack.headline(self.record) if self.record else []

    @property
    def human_minutes(self) -> float | None:
        steps = self.summary.get("human_steps")
        return None if steps is None else sum(step.get("minutes") or 0 for step in steps)


@dataclasses.dataclass
class Run:
    name: str
    info: dict[str, Any]
    groups: list[dict[str, Any]]
    cells: list[Cell]
    schema: int

    @property
    def href(self) -> str:
        return f"/runs/{self.name}/"

    @property
    def date(self) -> dt.date:
        return dt.date.fromisoformat(self.info["date"])

    @property
    def number(self) -> int:
        return int(self.info.get("number") or 0)

    @property
    def label(self) -> str:
        """'Oct 13, 2026 · #5', with the attempt when the run was re-run."""
        attempt = int(self.info.get("attempt") or 1)
        return f"{self.date:%b} {self.date.day}, {self.date.year} · #{self.number}" + (f".{attempt}" if attempt > 1 else "")

    @property
    def short_label(self) -> str:
        return f"{self.date:%b} {self.date.day} #{self.number}"

    @property
    def full(self) -> bool:
        return self.info.get("scope", FULL) == FULL

    @property
    def scope(self) -> str:
        return "Full run" if self.full else str(self.info.get("scope", "")).replace(" · ", ", ").capitalize()

    @property
    def finished(self) -> list[Cell]:
        return [c for c in self.cells if c.status != "missing"]

    def apps(self) -> list[str]:
        return list(dict.fromkeys(c.app for c in self.cells))

    def clouds(self) -> list[str]:
        return list(dict.fromkeys(c.cloud for c in self.cells))

    def cell(self, model: str, cloud: str, app: str, trial: int = 1) -> Cell | None:
        return next((c for c in self.cells if (c.model, c.cloud, c.app, int(c.trial)) == (model, cloud, app, trial)), None)

    def group(self, model: str, cloud: str) -> dict[str, Any] | None:
        return next((g for g in self.groups if (g["model"], g["cloud"]) == (model, cloud)), None)

    @property
    def agent_usd(self) -> float:
        return sum(c.agent_usd or 0 for c in self.finished)

    def technology_tally(self) -> dict[str, list[tuple[str, int]]]:
        """How many of the run's cells used each runtime, framework and data store."""
        return stack.tally([c.record for c in self.finished if c.record])

    @property
    def success_count(self) -> int:
        return sum(c.status == "success" for c in self.cells)

    @property
    def mean_score(self) -> float | None:
        scores = [c.score for c in self.finished if c.score is not None]
        return statistics.fmean(scores) if scores else None


def cell_slug(cell: dict[str, Any]) -> str:
    return f"{cell['model']}/{cell['cloud']}/{cell['app']}-t{cell['trial']}"


def load(results: Path) -> list[Run]:
    """Every run under results/runs, oldest first."""
    runs = []
    for summary_path in sorted((results / "runs").glob("*/summary.json")):
        summary = json.loads(summary_path.read_text())
        run = Run(name=summary["run"]["name"], info=summary["run"], groups=summary.get("groups") or [], cells=[],
                  schema=int(summary.get("schema") or 1))
        for row in summary.get("cells") or []:
            source = summary_path.parent / "cells" / cell_slug(row)
            record_path, report_path = source.with_suffix(".json"), source.with_suffix(".md")
            record = json.loads(record_path.read_text()) if record_path.is_file() else None
            report = report_path.read_text() if report_path.is_file() else ""
            run.cells.append(Cell(run=run, summary=row, record=record, report=report, source=source))
        runs.append(run)
    return sorted(runs, key=lambda r: (r.info["date"], r.number, int(r.info.get("attempt") or 1)))


# -- metrics ---------------------------------------------------------------------------------

def _human(group: dict[str, Any], key: str) -> float | None:
    steps = group.get("human_steps")
    return steps.get(key) if isinstance(steps, dict) else None


def _usage(entry: dict[str, Any], level: str) -> float | None:
    return (entry.get("hosting_usage_usd") or {}).get(level)


def _percent(value: float | None) -> float | None:
    return None if value is None else 100 * value


def _usd_tick(value: float) -> str:
    return f"${value:,.0f}" if value >= 10 or value == 0 else f"${value:,.2f}".rstrip("0").rstrip(".")


def _duration_tick(seconds: float) -> str:
    return f"{seconds / 60:.0f}m" if seconds >= 120 else f"{seconds:.0f}s"


@dataclasses.dataclass(frozen=True)
class Metric:
    id: str
    label: str
    description: str
    group: Callable[[dict[str, Any]], float | None]  # from a summary group (model x cloud)
    cell: Callable[[Cell], float | None]  # from one cell
    format: Callable[[float | None], str]
    tick: Callable[[float], str]
    better: str  # "higher" or "lower"
    top: float | None = None  # fixed axis maximum, for percentages and scores
    integer: bool = False  # counts, charted on whole-number ticks


def metrics(cfg: config.Config) -> list[Metric]:
    percent = lambda v: fmt.DASH if v is None else f"{v:.0f}%"  # noqa: E731
    common = [
        Metric("success", "Success rate", "Share of apps whose deployment passed every required check.",
               lambda g: _percent(g.get("success_rate")), lambda c: 100.0 if c.status == "success" else 0.0,
               percent, lambda v: f"{v:.0f}%", "higher", 100),
        Metric("checks", "Checks passed", "Share of the verifier's checks that passed, averaged over apps.",
               lambda g: _percent(g.get("mean_score")), lambda c: _percent(c.score), percent,
               lambda v: f"{v:.0f}%", "higher", 100),
        Metric("human_steps", "Human steps", "Things a person had to do, or would have to do, for the agent to deploy.",
               lambda g: _human(g, "count"), lambda c: None if c.human_steps is None else float(len(c.human_steps)),
               lambda v: fmt.DASH if v is None else f"{v:g}", lambda v: f"{v:g}", "lower", integer=True),
        Metric("human_minutes", "Human time", "Estimated minutes those human steps take.",
               lambda g: _human(g, "minutes"), lambda c: c.human_minutes, fmt.minutes, lambda v: f"{v:g}m", "lower"),
        Metric("security", "Security & compliance", "Score of the independent security and compliance review (0-100).",
               lambda g: g.get("security_score"), lambda c: c.summary.get("security_score"), fmt.score,
               lambda v: f"{v:.0f}", "higher", 100),
        Metric("stack_fit", "Stack fit", "The same review's rating of the stack the agent chose for each app, judged "
               "against the app's requirements (0-100). From benchmark version 2.",
               lambda g: g.get("stack_fit_score"), lambda c: c.summary.get("stack_fit_score"), fmt.score,
               lambda v: f"{v:.0f}", "higher", 100),
        Metric("build", "Build time", "Wall-clock time of the agent's build phase, averaged over apps.",
               lambda g: g.get("mean_build_s"), lambda c: c.build_s, fmt.duration, _duration_tick, "lower"),
        Metric("deploy", "Deploy time", "Wall-clock time of the agent's deploy phase, averaged over apps.",
               lambda g: g.get("mean_deploy_s"), lambda c: c.deploy_s, fmt.duration, _duration_tick, "lower"),
        Metric("tokens", "Tokens", "Tokens the agent used, including cache reads and writes; totals across apps.",
               lambda g: g.get("tokens"), lambda c: c.tokens, fmt.tokens, fmt.tokens, "lower"),
        Metric("agent_usd", "Agent cost", "Model API cost of the build and deploy sessions; totals across apps.",
               lambda g: g.get("agent_usd"), lambda c: c.agent_usd, fmt.usd, _usd_tick, "lower"),
    ]
    hosting = [
        Metric(f"hosting_{usage.id}", f"Hosting, {usage.label.lower()}",
               f"Estimated monthly hosting cost of the deployed resources: {usage.description[0].lower()}{usage.description[1:]}",
               (lambda g, level=usage.id: _usage(g, level)), (lambda c, level=usage.id: _usage(c.summary, level)),
               fmt.usd, _usd_tick, "lower")
        for usage in cfg.hosting_usage
    ]
    return common + hosting


@dataclasses.dataclass
class Series:
    key: str  # what the series is (a cloud id, or model/cloud)
    name: str
    color: int  # index into the site's palette
    values: list[float | None]


def trend(runs: list[Run], metric: Metric, cfg: config.Config, app: str | None = None) -> tuple[list[Run], list[Series]]:
    """The runs in scope and one series per model x cloud: across apps for full runs (`app` None),
    else for one app in every run that included it, averaged over trials."""
    scoped = [r for r in runs if (r.full if app is None else app in r.apps())]
    models = list(dict.fromkeys(c.model for r in scoped for c in r.cells))
    clouds = [x.id for x in cfg.clouds] + sorted({c.cloud for r in scoped for c in r.cells} - {x.id for x in cfg.clouds})
    series = []
    for model in models:
        for cloud in clouds:
            values = []
            for run in scoped:
                if app is None:
                    group = run.group(model, cloud)
                    values.append(metric.group(group) if group else None)
                else:
                    found = [metric.cell(c) for c in run.finished if (c.model, c.cloud, c.app) == (model, cloud, app)]
                    found = [v for v in found if v is not None]
                    values.append(statistics.fmean(found) if found else None)
            if any(v is not None for v in values):
                name = cloud_name(cfg, cloud) + (f" · {model_name(cfg, model)}" if len(models) > 1 else "")
                series.append(Series(f"{model}/{cloud}", name, clouds.index(cloud) + len(clouds) * models.index(model), values))
    return scoped, series


# -- names that survive config changes ---------------------------------------------------------

def cloud_name(cfg: config.Config, cloud_id: str) -> str:
    return next((x.name for x in cfg.clouds if x.id == cloud_id), cloud_id)


def cloud_url(cfg: config.Config, cloud_id: str) -> str | None:
    return next((x.url for x in cfg.clouds if x.id == cloud_id), None)


def app_name(cfg: config.Config, app_id: str, short: bool = True) -> str:
    app = next((a for a in cfg.apps if a.id == app_id), None)
    if app is None:
        return app_id
    return (app.short or app.name) if short else app.name


def model_name(cfg: config.Config, model_id: str, label: bool = False) -> str:
    model = next((m for m in cfg.models if m.id == model_id), None)
    if model is None:
        return model_id
    return model.label if label else model.name


def cloud_color(cfg: config.Config, cloud_id: str) -> int:
    ids = [x.id for x in cfg.clouds]
    return ids.index(cloud_id) if cloud_id in ids else len(ids)
