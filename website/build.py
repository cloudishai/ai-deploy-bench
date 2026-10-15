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
# Markdown links that point somewhere relative: into the repository, or next to a cell's report.
RELATIVE_LINK = re.compile(r"(!?\[[^\]]*\])\((?![a-z]+:|#|/)([^)\s]+)\)")
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


def absolute_links(text: str, base: str, local: dict[str, str] | None = None) -> str:
    """Points a markdown document's relative links at the repository on GitHub, relative to `base`
    (a folder in the repository), so the document reads the same wherever it's fetched from. `local`
    maps a link's first path segment to a URL on the site instead (a cell's screenshots)."""
    def resolve(match: re.Match) -> str:
        label, href = match.groups()
        path, _, anchor = href.partition("#")
        head, _, rest = path.partition("/")
        if local and head in local:
            return f"{label}({local[head]}{rest})"
        resolved = os.path.normpath(os.path.join(base, path)).replace(os.sep, "/")
        return f"{label}({GITHUB}/blob/main/{resolved}" + (f"#{anchor}" if anchor else "") + ")"
    return RELATIVE_LINK.sub(resolve, text)


def md_cell(value: Any) -> str:
    """Text that can sit in a markdown table cell."""
    return " ".join(str(value).split()).replace("|", "\\|")


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
        self.pages: list[tuple[str, str | None]] = []  # (URL path, last modified) for the sitemap
        self.markdown: dict[str, str] = {}  # each page's markdown version, by URL path
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
            url=lambda path: SITE_URL + path, md=lambda href: f"{SITE_URL}{href}index.md",
        )
        self.env.filters["md_cell"] = md_cell
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

    def write(self, path: str, template: str, lastmod: str | None = None, markdown: str | None = None,
              **context: Any) -> None:
        """Writes a page and, next to it, its markdown version (`index.md`): from the `markdown` text, or
        else rendered from the template of the same name under templates/md/."""
        target = self.out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.env.get_template(template).render(page=path, **context))
        if not path.endswith("index.html"):
            return
        url = "/" + path[: -len("index.html")]
        self.pages.append((url, lastmod))
        if markdown is None:
            markdown = self.env.get_template(f"md/{template.removesuffix('.html')}.md").render(page=path, **context)
        markdown = "\n".join(line.rstrip() for line in markdown.splitlines())
        markdown = re.sub(r"^(#{1,6} .+)\n(?=\S)", r"\1\n\n", markdown, flags=re.MULTILINE)  # a blank line after headings
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
        (target.parent / "index.md").write_text(markdown)
        self.markdown[url] = markdown

    def dataset(self, name: str, description: str, path: str, runs: list[data.Run], json_path: str,
                **extra: Any) -> dict[str, Any]:
        """schema.org Dataset metadata (JSON-LD), so search engines and agents can tell what the data is."""
        dates = sorted(r.info["date"] for r in runs)
        found = {
            "@context": "https://schema.org", "@type": "Dataset", "name": name, "description": description,
            "url": SITE_URL + path, "isAccessibleForFree": True, "isBasedOn": GITHUB,
            "creator": {"@type": "Organization", "name": "AI Deploy Bench", "url": SITE_URL},
            "keywords": ["AI coding agents", "cloud deployment", "benchmark", "Claude Code"]
                        + [x.name for x in self.cfg.clouds],
            "variableMeasured": [m.label for m in self.metrics],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE_URL + json_path},
                {"@type": "DataDownload", "encodingFormat": "text/markdown", "contentUrl": f"{SITE_URL}{path}index.md"},
            ],
            **extra,
        }
        if dates:
            found["temporalCoverage"] = dates[0] if dates[0] == dates[-1] else f"{dates[0]}/{dates[-1]}"
            found["dateModified"] = dates[-1]
        return found

    def cell_markdown(self, run: data.Run, cell: data.Cell) -> str:
        """The cell's report, with where it sits on the site and its screenshots' and records' links."""
        title, _, body = (cell.report or f"# {data.app_name(self.cfg, cell.app, False)} on "
                          f"{data.cloud_name(self.cfg, cell.cloud)}\n").partition("\n")
        context = (f"> {data.app_name(self.cfg, cell.app, False)} on {data.cloud_name(self.cfg, cell.cloud)}, built and "
                   f"deployed by {data.model_name(self.cfg, cell.model, True)} in benchmark run {run.label}: "
                   f"{STATES[state(cell)][0].lower()}, {cell.checks_passed}/{cell.checks_total} checks passed.\n>\n"
                   f"> [Web page]({SITE_URL}{cell.href}) · [Full record (JSON)]({SITE_URL}/data/runs/{run.name}/cells/"
                   f"{cell.slug}.json) · [Run]({SITE_URL}{run.href}index.md) · "
                   f"[{data.cloud_name(self.cfg, cell.cloud)} on every run]({SITE_URL}/clouds/{cell.cloud}/index.md)")
        if cell.from_run:
            context += (f"\n>\n> This run reran other clouds, so this result is copied unchanged from run "
                        f"[#{cell.from_run.get('number')}]({SITE_URL}/runs/{cell.from_run.get('name')}/index.md).")
        body = absolute_links(body, f"results/runs/{run.name}/cells/{cell.model}/{cell.cloud}",
                              local={f"{cell.app}-t{cell.trial}": f"{SITE_URL}{cell.href}"})
        return f"{title}\n\n{context}\n{body}"

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
        # Every page but a run's own changes when a run is added, so the newest run's date is theirs.
        updated = self.runs[-1].info["date"] if self.runs else None
        names = [x.name for x in self.cfg.clouds]
        description = ("What it takes for an AI coding agent to build web apps from a written spec and deploy them to "
                       + (", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else "".join(names)) + ": success, deploys without a human, human steps "
                       "and time, security, stack fit, time, tokens and cost, for every run, cloud and app.")
        home_ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "AI Deploy Bench", "url": SITE_URL + "/",
                    "description": description},
                   self.dataset("AI Deploy Bench results", description, "/", self.runs, "/data/index.json")]
        self.write("index.html", "home.html", latest=latest, full_runs=full, preview=preview, preview_app=featured,
                   lastmod=updated, ld=home_ld)
        self.write("runs/index.html", "runs.html", lastmod=updated)
        for run in self.runs:
            self.write(f"runs/{run.name}/index.html", "run.html", run=run, lastmod=run.info["date"], ld=self.dataset(
                f"AI Deploy Bench run {run.label}", f"Results of benchmark run {run.label} ({run.scope.lower()}): each app "
                f"built and deployed on each cloud, verified live.", run.href, [run], f"/data/runs/{run.name}/summary.json"))
            for cell in run.cells:
                if cell.status == "missing":
                    continue
                self.write(f"runs/{run.name}/{cell.slug}/index.html", "cell.html", run=run, cell=cell,
                           commands=shell_commands(cell), lastmod=run.info["date"], markdown=self.cell_markdown(run, cell))
                for shot in cell.screenshots:
                    shutil.copyfile(shot["path"], self.out / "runs" / run.name / cell.slug / shot["name"])
        self.write("clouds/index.html", "clouds.html", latest=latest, lastmod=updated)
        for cloud in self.clouds():
            history = [run for run in self.runs if cloud in run.clouds()]
            cloud_latest = next((r for r in reversed(history) if r.full), history[-1] if history else None)
            name = data.cloud_name(self.cfg, cloud)
            self.write(f"clouds/{cloud}/index.html", "cloud.html", cloud=cloud, history=history, latest=cloud_latest,
                       lastmod=history[-1].info["date"] if history else updated, ld=self.dataset(
                           f"AI Deploy Bench results for {name}", f"How an AI coding agent did building and deploying web "
                           f"apps on {name}, in every run of the benchmark.", f"/clouds/{cloud}/", history,
                           "/data/index.json", about={"@type": "Organization", "name": name,
                                                      "url": data.cloud_url(self.cfg, cloud)}))
        self.write("trends/index.html", "trends.html", app=None, charts=self.charts(None), lastmod=updated)
        for app in self.cfg.apps:
            self.write(f"trends/{app.id}/index.html", "trends.html", app=app.id, charts=self.charts(app.id),
                       lastmod=updated)
        methodology = (ROOT / "docs" / "methodology.md").read_text()
        self.write("methodology/index.html", "methodology.html", body=markdown(methodology, base="docs"),
                   markdown=absolute_links(methodology, "docs"))
        (self.out / "404.html").write_text(self.env.get_template("404.html").render(page="404.html"))
        self.copy_data()
        self.write_agent_files(latest)
        urls = "".join(f"<url><loc>{xml_escape(SITE_URL + page)}</loc>" + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "")
                       + "</url>" for page, lastmod in self.pages)
        (self.out / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')

    def write_agent_files(self, latest: data.Run | None) -> None:
        """llms.txt (an index for language models, https://llmstxt.org), llms-full.txt (the main pages'
        markdown in one file) and robots.txt."""
        (self.out / "llms.txt").write_text(self.env.get_template("llms.txt").render(page="llms.txt", latest=latest))
        full = ["/", "/methodology/"] + ([latest.href] if latest else []) + ["/clouds/"] + [f"/clouds/{c}/" for c in self.clouds()]
        parts = [f"<!-- {SITE_URL}{url}index.md -->\n\n{self.markdown[url]}" for url in full if url in self.markdown]
        (self.out / "llms-full.txt").write_text("\n---\n\n".join(parts))
        (self.out / "robots.txt").write_text(
            "# AI Deploy Bench is an open benchmark: search engines, AI agents and crawlers are all welcome.\n"
            f"# For language models: {SITE_URL}/llms.txt indexes the site, {SITE_URL}/llms-full.txt has its main\n"
            "# pages in one file, every page has a markdown version at <page>/index.md (or send\n"
            f"# `Accept: text/markdown`), and the raw results are JSON under {SITE_URL}/data/.\n"
            "User-agent: *\n"
            "Content-Signal: search=yes, ai-input=yes\n"
            "Allow: /\n\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")

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
