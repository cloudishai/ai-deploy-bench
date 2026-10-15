"""The website: built from the committed results, every internal link resolves and pages stay within
the CSP (no inline scripts or styles); charts, trends and the deploy script."""

import io
import json
import re
import shutil
import tarfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import httpx
import pytest

from markupsafe import escape

from bench import config
from website import build, charts, data, deploy

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r'(?:href|src)="([^"]+)"')


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    built = build.Site(ROOT / "results", out)
    built.build()
    return built


def html_pages(out: Path) -> list[Path]:
    return sorted(out.rglob("*.html"))


def test_every_run_and_cell_has_a_page(site):
    assert site.runs, "the repository has committed runs"
    for run in site.runs:
        assert (site.out / "runs" / run.name / "index.html").is_file()
        for cell in run.cells:
            if cell.status != "missing":
                page = site.out / "runs" / run.name / cell.slug / "index.html"
                assert page.is_file()
                for shot in cell.screenshots:
                    assert (page.parent / shot["name"]).is_file()
    for path in ("index.html", "404.html", "trends/index.html", "runs/index.html", "methodology/index.html",
                 "sitemap.xml", "robots.txt", "data/runs.json", "favicon.svg"):
        assert (site.out / path).is_file(), path


def test_all_cells_table_rows_link_to_the_cell_page(site):
    """Each finished cell's row in a run's 'All cells' table is clickable and lands on its drill-down
    page (which carries the checks breakdown). data-href drives the row-wide click in app.js."""
    hrefs = re.compile(r'<tr class="row-link" data-href="([^"]+)"')
    for run in site.runs:
        finished = [c for c in run.cells if c.status != "missing"]
        if not finished:
            continue
        page = (site.out / "runs" / run.name / "index.html").read_text()
        targets = hrefs.findall(page)
        assert len(targets) == len(finished), run.name
        for target in targets:
            assert (site.out / target.strip("/") / "index.html").is_file(), target
    # app.js carries the row-click behaviour (no inline script, per the CSP).
    assert "tr.row-link" in (site.out / "static" / "app.js").read_text()


def test_internal_links_resolve(site):
    broken = []
    for page in html_pages(site.out):
        for target in LINK.findall(page.read_text()):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = target.split("#")[0].split("?")[0]
            resolved = site.out / path.lstrip("/") if path.startswith("/") else page.parent / path
            if resolved.is_dir():
                resolved = resolved / "index.html"
            if not resolved.is_file():
                broken.append(f"{page.relative_to(site.out)} -> {target}")
    assert broken == []


def test_pages_need_nothing_the_csp_forbids(site):
    for page in html_pages(site.out):
        text = page.read_text()
        assert " style=" not in text, page
        assert not re.search(r"<script(?![^>]*\bsrc=)", text), page  # only external scripts
        assert "<style" not in text, page


def test_charts_are_valid_svg(site):
    text = (site.out / "trends" / "index.html").read_text()
    svgs = re.findall(r"<svg class=\"chart.*?</svg>", text, flags=re.DOTALL)
    assert len(svgs) == len(site.metrics)
    for svg in svgs:
        ElementTree.fromstring(svg.replace('class="chart', 'xmlns="http://www.w3.org/2000/svg" class="chart', 1))


def test_old_schemas_render(site):
    oldest = site.runs[0]
    page = (site.out / "runs" / oldest.name / oldest.cells[0].slug / "index.html").read_text()
    assert "Checks" in page and "Raw data" in page


def test_version_2_runs_show_stack_fit(tmp_path):
    results = tmp_path / "results"
    latest = sorted((ROOT / "results" / "runs").glob("*/summary.json"))[-1].parent
    shutil.copytree(latest, results / "runs" / latest.name)
    summary_path = results / "runs" / latest.name / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["run"]["benchmark_version"] = 2
    summary["groups"][0]["stack_fit_score"] = 72.0
    row = next(c for c in summary["cells"] if c.get("path"))
    row["stack_fit_score"] = 72.0
    summary_path.write_text(json.dumps(summary))
    record_path = summary_path.parent / row["path"]
    record = json.loads(record_path.read_text())
    record["stack_fit"] = {"status": "completed", "score": 72.0, "summary": "A static site would have done.",
                           "criteria": [{"id": "fit", "name": "Fit for the job", "weight": 40, "score": 8, "rationale": "ok"}]}
    record_path.write_text(json.dumps(record))
    built = build.Site(results, tmp_path / "site")
    built.build()
    run = built.runs[0]
    cell = next(c for c in run.cells if c.slug == data.cell_slug(row))
    page = (built.out / "runs" / run.name / cell.slug / "index.html").read_text()
    assert "<h2>Stack fit</h2>" in page and "A static site would have done." in page and "72/100" in page
    assert "benchmark v2" in (built.out / "runs" / run.name / "index.html").read_text()


def test_deploys_with_and_without_a_human_are_shown_from_version_3(site):
    run = next(r for r in site.runs if r.name == "2026-10-15_15-1")
    groups = {g["cloud"]: g for g in run.groups}
    # Cloudish deployed everything without credentials; the others needed a person's token, and Vercel's
    # CRUD app failed even with it.
    assert groups["cloudish"]["deploys_with_human"] == {"count": 0, "total": 0}
    assert groups["vercel"]["deploys_with_human"] == {"count": 4, "total": 5}
    assert run.cell("opus-5-5", "cloudish", "static").with_human == "not_needed"
    vercel_crud = run.cell("opus-5-5", "vercel", "crud")
    assert (vercel_crud.without_human, vercel_crud.with_human) == ("failed", "failed")
    page = (site.out / "runs" / run.name / "index.html").read_text()
    assert "<th>With a human</th>" in page and "Not needed" in page
    assert '<span class="outcome outcome-partial"><span aria-hidden="true">◐</span> 4/5</span>' in page
    cell_page = (site.out / "runs" / run.name / vercel_crud.slug / "index.html").read_text()
    assert "Deploy with a human" in cell_page
    # Runs before version 3 didn't make the attempt without credentials, so they show neither.
    old = site.runs[0]
    assert all(c.with_human is None for c in old.cells)
    assert "Deploys with a human" not in (site.out / "runs" / old.name / "index.html").read_text()


def test_technologies_are_shown_for_every_cell_with_a_record(site):
    for run in site.runs:
        for cell in run.finished:
            page = (site.out / "runs" / run.name / cell.slug / "index.html").read_text()
            assert "<h2>Technologies</h2>" in page
            for names in cell.technologies.values():
                for name in names:
                    assert f'<span class="chip">{escape(name)}</span>' in page
    home = (site.out / "index.html").read_text()
    if site.runs[-1].technology_tally():
        assert "What the agents built with" in home and 'class="chip-count"' in home
    # The app x cloud grid fits the page: no scroll container around it.
    assert 'class="matrix cols-' in home and "table-scroll\">\n<div class=\"matrix" not in home


def test_cell_text_is_escaped_and_markdown_has_no_raw_html():
    rendered = build.markdown("**done** <script>alert(1)</script> [docs](../apps/static/TASK.md)", base="docs")
    assert "<strong>done</strong>" in rendered and "<script>" not in rendered
    assert 'href="https://github.com/' in rendered and "/blob/main/apps/static/TASK.md" in rendered


def test_line_chart_handles_gaps_single_points_and_ties():
    series = [data.Series("a", "A", 0, [1.0, None, 3.0]), data.Series("b", "B", 1, [1.0, 2.0, None])]
    svg = str(charts.line_chart(["r1", "r2", "r3"], series, str, str, "Title"))
    ElementTree.fromstring(svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1))
    assert svg.count("<circle") == 4 and "<polyline" in svg  # B's two points join; A's are split by a gap
    cx = re.findall(r'<circle class="dot" cx="([\d.]+)" cy="([\d.]+)"', svg)
    assert cx[0][1] == cx[2][1] and cx[0][0] != cx[2][0]  # equal values at r1 are nudged apart
    assert "No data yet" in charts.line_chart(["r1"], [data.Series("a", "A", 0, [None])], str, str, "Empty")
    integer = str(charts.line_chart(["r1"], [data.Series("a", "A", 0, [3.0])], str, lambda v: f"{v:g}", "Steps", integer=True))
    assert ">4<" in integer and ">1<" in integer and ">0.8<" not in integer


def test_trends_compare_full_runs_across_apps_and_any_run_per_app(site):
    cfg = config.load()
    success = next(m for m in site.metrics if m.id == "success")
    runs, series = data.trend(site.runs, success, cfg)
    assert all(r.full for r in runs)
    static_runs, static = data.trend(site.runs, success, cfg, "static")
    assert len(static_runs) >= len(runs) and all("static" in r.apps() for r in static_runs)
    assert all(len(s.values) == len(static_runs) for s in static)


# -- deploy -----------------------------------------------------------------------------------

def built_dist(tmp_path, sha="abc1234def"):
    dist = tmp_path / "dist"
    (dist / "static").mkdir(parents=True)
    (dist / "index.html").write_text(f'<html><head><meta name="build" content="{sha}"></head></html>')
    (dist / "static" / "style.css").write_text("body {}")
    return dist


class FakeCloudish:
    def __init__(self, build_states=("running", "succeeded"), domains=()):
        self.calls, self.uploads, self.build_states = [], [], list(build_states)
        self.domains = {d["host"]: d for d in domains}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        method, path = request.method, request.url.path.removeprefix("/api/v1")
        self.calls.append((method, path))
        assert request.headers["authorization"] == "Bearer cld_test"
        if (method, path) == ("GET", "/me"):
            return httpx.Response(200, json={"apiKey": {"alias": "ai-deploy-bench"}})
        if (method, path) == ("POST", "/projects"):
            self.uploads.append(request.read())
            return httpx.Response(201, json={"project": {"path": "ai-deploy-bench/aideploybench"}, "build": {"id": 7}})
        if (method, path) == ("GET", "/images/builds/7"):
            state = self.build_states.pop(0)
            return httpx.Response(200, json={"build": {"status": state, "logs": f"step {state}\n",
                                                       "error": "boom" if state == "failed" else None}})
        if (method, path) == ("GET", "/projects/ai-deploy-bench/aideploybench"):
            return httpx.Response(200, json={"subdomain": {"url": "https://aideploybench.on.do.cloudish.ai/"}})
        if (method, path) == ("GET", "/projects/ai-deploy-bench/aideploybench/domains"):
            return httpx.Response(200, json={"domains": list(self.domains.values())})
        if (method, path) == ("POST", "/projects/ai-deploy-bench/aideploybench/domains"):
            body = json.loads(request.content)
            domain = {"host": body["host"], "status": "pending", "redirect": body["redirect"],
                      "txtRecord": {"name": f"_cloudish-challenge.{body['host']}", "value": "cloudish-verify=x"}}
            self.domains[body["host"]] = domain
            return httpx.Response(201, json={"domain": domain})
        return httpx.Response(404, json={"error": f"unexpected {method} {path}"})


def test_deploy_builds_configures_domains_and_waits_for_the_new_build(tmp_path):
    dist = built_dist(tmp_path)
    cloudish = FakeCloudish(domains=[{"host": "aideploybench.com", "status": "active", "redirect": False}])
    served = iter(["old000", "abc1234def"])
    site = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text=f'<meta name="build" content="{next(served)}">')))
    lines = []
    url = deploy.deploy(deploy.Cloudish("cld_test", transport=httpx.MockTransport(cloudish)), dist, site=site,
                        log=lines.append, sleep=lambda s: None)
    assert url == "https://aideploybench.on.do.cloudish.ai"
    # Only the missing domain is added, as a redirect to the primary one; its DNS records are printed.
    assert cloudish.calls.count(("POST", "/projects/ai-deploy-bench/aideploybench/domains")) == 1
    assert cloudish.domains["www.aideploybench.com"]["redirect"] is True
    assert any("TXT _cloudish-challenge.www.aideploybench.com" in line for line in lines)
    assert any("CNAME www.aideploybench.com -> do.cloudish.ai" in line for line in lines)
    # The upload is a build context with the Dockerfile at its root and the site under dist/.
    body = cloudish.uploads[0]
    assert b'name="access"' in body and b"open" in body
    start = body.index(b"\x1f\x8b")
    with tarfile.open(fileobj=io.BytesIO(body[start:]), mode="r:*") as tar:
        names = tar.getnames()
    assert {"Dockerfile", "nginx.conf", "dist/index.html", "dist/static/style.css"} <= set(names)


def test_a_failed_build_stops_the_deploy(tmp_path):
    cloudish = FakeCloudish(build_states=["failed"])
    with pytest.raises(deploy.DeployError, match="build 7 failed: boom"):
        deploy.deploy(deploy.Cloudish("cld_test", transport=httpx.MockTransport(cloudish)), built_dist(tmp_path),
                      log=lambda line: None, sleep=lambda s: None)
    assert ("GET", "/projects/ai-deploy-bench/aideploybench/domains") not in cloudish.calls


def test_deploy_refuses_an_unbuilt_site(tmp_path):
    with pytest.raises(deploy.DeployError, match="run python -m website.build first"):
        deploy.build_context(tmp_path)
