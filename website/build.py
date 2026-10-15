"""Builds the static site from results/: python -m website.build [--out website/dist]."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import jinja2
from markdown_it import MarkdownIt
from markupsafe import Markup

from bench import config, fmt
from website import charts, data

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
REPO = os.environ.get("GITHUB_REPOSITORY", "cloudishai/ai-deploy-bench")
GITHUB = f"https://github.com/{REPO}"
SITE_URL = "https://aideploybench.com"

STATES = {
    "success": ("Success", "Deployed and passed every required check"),
    "partial": ("Partial", "Reachable, but at least one required check failed"),
    "failed": ("Failed", "No reachable deployment"),
    "human": ("Needs a person", "Couldn't finish without a step only a person can do"),
    "error": ("Error", "The agent or the harness couldn't run"),
    "missing": ("Missing", "No result was recorded"),
}
# How the deploy attempt with no credentials went: (symbol, label, tooltip).
OUTCOMES = {
    "success": ("✓", "Deployed", "Deployed with no credentials provided, and passed every required check"),
    "failed": ("✗", "Needed a person", "Couldn't deploy until a person provided the cloud's credentials"),
}
SEVERITIES = ("critical", "high", "medium", "low", "info")
PREVIEW = ("success", "human_minutes", "security", "agent_usd")  # the charts on the overview
COMMAND = re.compile(r"^- `([^`]*)` (❌ )?`(.*)`$")


def state(cell: data.Cell) -> str:
    """What a cell's badge shows: its status, or `human` when it was blocked on a person."""
    if cell.status not in ("success", "missing") and cell.failure_stage == "human":
        return "human"
    return cell.status if cell.status in STATES else "error"


def markdown(text: str, base: str | None = None) -> Markup:
    """Renders markdown without raw HTML (agent text is data, not markup). With `base`, relative links
    point into the repository on GitHub, relative to that folder."""
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    if base is not None:
        default = md.renderer.rules.get("link_open")

        def link_open(tokens, idx, options, env):
            href = tokens[idx].attrGet("href") or ""
            if href and not re.match(r"^([a-z]+:|#|/)", href):
                path, _, anchor = href.partition("#")
                resolved = os.path.normpath(os.path.join(base, path)).replace(os.sep, "/")
                tokens[idx].attrSet("href", f"{GITHUB}/blob/main/{resolved}" + (f"#{anchor}" if anchor else ""))
            return default(tokens, idx, options, env) if default else md.renderer.renderToken(tokens, idx, options, env)

        md.renderer.rules["link_open"] = link_open
    return Markup(md.render(text or ""))


def report_section(report: str, heading: str) -> str:
    """The body of one `## heading` section of a cell's markdown report."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", report, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def shell_commands(cell: data.Cell) -> list[dict[str, Any]]:
    commands = []
    for line in report_section(cell.report, "Shell commands during deploy").splitlines():
        if match := COMMAND.match(line.strip()):
            commands.append({"at": match.group(1), "failed": bool(match.group(2)), "command": match.group(3)})
        elif line.startswith("- … "):
            commands.append({"at": "", "failed": False, "command": line[2:], "more": True})
    return commands


def human(group: dict[str, Any]) -> tuple[int | None, float | None]:
    """A summary group's (human steps, minutes)."""
    steps = group.get("human_steps")
    return (steps.get("count"), steps.get("minutes")) if isinstance(steps, dict) else (None, None)


def build_info() -> dict[str, str]:
    """The commit the site is built from (the deploy checks it's the one being served)."""
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = os.environ.get("GITHUB_SHA", "unknown")
    return {"sha": sha, "short": sha[:7], "time": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}


class Site:
    def __init__(self, results: Path, out: Path) -> None:
        self.results, self.out = results, out
        self.cfg = config.load()
        self.runs = data.load(results)
        self.metrics = data.metrics(self.cfg)
        self.pages: list[str] = []
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(HERE / "templates"),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )
        self.env.globals.update(
            cfg=self.cfg, runs=self.runs, fmt=fmt, github=GITHUB, site_url=SITE_URL, build=build_info(),
            states=STATES, outcomes=OUTCOMES, severities=SEVERITIES, state=state, markdown=markdown, bar=charts.bar, human=human,
            cloud_name=lambda c: data.cloud_name(self.cfg, c), cloud_url=lambda c: data.cloud_url(self.cfg, c),
            cloud_color=lambda c: data.cloud_color(self.cfg, c), app_name=lambda a, short=True: data.app_name(self.cfg, a, short),
            model_name=lambda m, label=False: data.model_name(self.cfg, m, label), metric_value=self.metric_value,
            hosting=self.hosting, asset=self.asset, trend_apps=self.trend_apps, compare=self.compare,
            cloud_href=lambda c: f"/clouds/{c}/", human_steps=lambda cells: data.human_steps(cells, self.cfg),
        )
        self.assets: dict[str, str] = {}

    # -- helpers for templates ---------------------------------------------------------------

    def asset(self, name: str) -> str:
        return f"/static/{name}?v={self.assets[name]}"

    def metric_value(self, metric: data.Metric, entry: Any) -> str:
        value = metric.cell(entry) if isinstance(entry, data.Cell) else metric.group(entry)
        return metric.format(value)

    def hosting(self, entry: dict[str, Any]) -> list[tuple[str, str]]:
        """(label, cost) per traffic level, or the older always-on estimate."""
        usage = entry.get("hosting_usage_usd") or {}
        if usage:
            return [(u.label, fmt.usd(usage.get(u.id))) for u in self.cfg.hosting_usage if u.id in usage]
        return [("Always on", fmt.usd(entry.get("hosting_monthly_usd")))]

    def compare(self, run: data.Run, model: str) -> list[dict[str, Any]]:
        """One row per metric with each cloud's value in `run` (in `run.clouds()` order), the best marked.
        Success and deploys without a human read as counts of apps, like the README."""
        groups = [run.group(model, cloud) for cloud in run.clouds()]
        rows = []
        for metric in self.metrics:
            values = [metric.group(g) if g else None for g in groups]
            if all(v is None for v in values):
                continue
            known = [v for v in values if v is not None]
            best = (max if metric.better == "higher" else min)(known) if len(known) > 1 else None
            texts = [metric.format(v) for v in values]
            if metric.id == "success":
                texts = [f"{g.get('success', 0)}/{g.get('cells', 0)}" if g else fmt.DASH for g in groups]
            elif metric.id == "no_human":
                texts = [f"{(g.get('deploys_without_human') or {}).get('count')}/{(g.get('deploys_without_human') or {}).get('total')}"
                         if g and g.get("deploys_without_human") else fmt.DASH for g in groups]
            label = "Success" if metric.id == "success" else metric.label
            rows.append({"label": label, "description": metric.description, "better": metric.better,
                         "values": [{"text": t, "best": best is not None and v == best} for t, v in zip(texts, values)]})
        return rows

    def trend_apps(self) -> list[tuple[str, str, int]]:
        """(app id, name, runs with it) for the per-app trend pages."""
        found = []
        for app in self.cfg.apps:
            count = sum(app.id in r.apps() for r in self.runs)
            found.append((app.id, app.short or app.name, count))
        return found

    # -- output ------------------------------------------------------------------------------

    def clouds(self) -> list[str]:
        """Every cloud in benchmark.yaml, then any that only older runs have."""
        ids = [x.id for x in self.cfg.clouds]
        return ids + sorted({c.cloud for r in self.runs for c in r.cells} - set(ids))

    def write(self, path: str, template: str, **context: Any) -> None:
        target = self.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.env.get_template(template).render(page=path, **context))
        if path.endswith("index.html"):
            self.pages.append("/" + path[: -len("index.html")])

    def charts(self, app: str | None) -> list[dict[str, Any]]:
        found = []
        for metric in self.metrics:
            runs, series = data.trend(self.runs, metric, self.cfg, app)
            labels = [r.short_label for r in runs]
            found.append({"metric": metric, "series": series, "runs": runs,
                          "svg": charts.line_chart(labels, series, metric.format, metric.tick, metric.label, metric.top,
                                                   metric.integer)})
        return found

    def build(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        static = self.out / "static"
        static.mkdir(parents=True)
        for source in sorted((HERE / "static").iterdir()):
            shutil.copyfile(source, static / source.name)
            self.assets[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()[:10]
        shutil.copyfile(HERE / "static" / "favicon.svg", self.out / "favicon.svg")

        full = [r for r in self.runs if r.full]
        latest = full[-1] if full else (self.runs[-1] if self.runs else None)
        featured = None if full else max(self.trend_apps(), key=lambda a: a[2], default=(None,))[0]
        preview = [c for c in self.charts(None if full else featured) if c["metric"].id in PREVIEW] if self.runs else []
        self.write("index.html", "home.html", latest=latest, full_runs=full, preview=preview, preview_app=featured)
        self.write("runs/index.html", "runs.html")
        for run in self.runs:
            self.write(f"runs/{run.name}/index.html", "run.html", run=run)
            for cell in run.cells:
                if cell.status == "missing":
                    continue
                self.write(f"runs/{run.name}/{cell.slug}/index.html", "cell.html", run=run, cell=cell,
                           commands=shell_commands(cell))
                for shot in cell.screenshots:
                    shutil.copyfile(shot["path"], self.out / "runs" / run.name / cell.slug / shot["name"])
        self.write("clouds/index.html", "clouds.html", latest=latest)
        for cloud in self.clouds():
            history = [run for run in self.runs if cloud in run.clouds()]
            cloud_latest = next((r for r in reversed(history) if r.full), history[-1] if history else None)
            self.write(f"clouds/{cloud}/index.html", "cloud.html", cloud=cloud, history=history, latest=cloud_latest)
        self.write("trends/index.html", "trends.html", app=None, charts=self.charts(None))
        for app in self.cfg.apps:
            self.write(f"trends/{app.id}/index.html", "trends.html", app=app.id, charts=self.charts(app.id))
        methodology = (ROOT / "docs" / "methodology.md").read_text()
        self.write("methodology/index.html", "methodology.html", body=markdown(methodology, base="docs"))
        (self.out / "404.html").write_text(self.env.get_template("404.html").render(page="404.html"))
        self.copy_data()
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
        urls = "".join(f"<url><loc>{xml_escape(SITE_URL + page)}</loc></url>" for page in self.pages)
        (self.out / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')

    def copy_data(self) -> None:
        """The results' JSON under /data/, for tools that read the benchmark."""
        for path in sorted(self.results.rglob("*.json")):
            target = self.out / "data" / path.relative_to(self.results)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        runs = [{"name": r.name, "label": r.label, "scope": r.info.get("scope"), "summary": f"/data/runs/{r.name}/summary.json"}
                for r in reversed(self.runs)]
        (self.out / "data" / "runs.json").write_text(json.dumps({"runs": runs}, indent=2) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m website.build", description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--out", type=Path, default=HERE / "dist")
    args = parser.parse_args(argv)
    site = Site(args.results, args.out)
    site.build()
    print(f"built {len(site.pages)} pages from {len(site.runs)} run(s) into {args.out}")


if __name__ == "__main__":
    main()
