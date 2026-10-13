from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from bench.verify.base import CheckFailed, Verifier, expect, expect_html, expect_json, expect_status

DATASET = Path(__file__).resolve().parents[2] / "apps" / "dataviz" / "fixtures" / "data" / "sales.csv"

QUERIES = {
    "summary_all": {},
    "summary_region": {"region": "West"},
    "summary_category": {"category": "Electronics"},
    "summary_combined": {"region": "East", "category": "Furniture", "start": "2025-03-01", "end": "2025-06-30"},
    "summary_empty": {"region": "Atlantis"},
}


def load_rows(path: Path = DATASET) -> list[dict]:
    with path.open(newline="") as f:
        return [
            {**row, "units": int(row["units"]), "revenue": float(row["revenue"])}
            for row in csv.DictReader(f)
        ]


def expected_summary(rows: list[dict], params: dict[str, str]) -> dict:
    matched = [
        r
        for r in rows
        if r["region"] == params.get("region", r["region"])
        and r["category"] == params.get("category", r["category"])
        and params.get("start", r["date"]) <= r["date"] <= params.get("end", r["date"])
    ]
    by_month: dict[str, float] = defaultdict(float)
    by_category: dict[str, float] = defaultdict(float)
    for r in matched:
        by_month[r["date"][:7]] += r["revenue"]
        by_category[r["category"]] += r["revenue"]
    return {
        "total_revenue": round(sum(r["revenue"] for r in matched), 2),
        "orders": len(matched),
        "units": sum(r["units"] for r in matched),
        "revenue_by_month": [{"month": m, "revenue": round(v, 2)} for m, v in sorted(by_month.items())],
        "revenue_by_category": [
            {"category": c, "revenue": round(v, 2)} for c, v in sorted(by_category.items(), key=lambda kv: -kv[1])
        ],
    }


def close(actual, expected: float) -> bool:
    return isinstance(actual, (int, float)) and abs(actual - expected) <= max(0.05, abs(expected) * 1e-6)


def compare(actual: dict, expected: dict) -> list[str]:
    """Returns human-readable differences; an empty list means the summary is correct."""
    if not isinstance(actual, dict):
        return [f"expected a JSON object, got {type(actual).__name__}"]
    problems = []
    if not close(actual.get("total_revenue"), expected["total_revenue"]):
        problems.append(f"total_revenue {actual.get('total_revenue')!r} != {expected['total_revenue']}")
    for field in ("orders", "units"):
        if actual.get(field) != expected[field]:
            problems.append(f"{field} {actual.get(field)!r} != {expected[field]}")
    for field, key in (("revenue_by_month", "month"), ("revenue_by_category", "category")):
        got = actual.get(field)
        if not isinstance(got, list):
            problems.append(f"{field} is not a list")
            continue
        got_keys = [item.get(key) for item in got if isinstance(item, dict)]
        want_keys = [item[key] for item in expected[field]]
        if got_keys != want_keys:
            problems.append(f"{field} order/keys {got_keys} != {want_keys}")
            continue
        for item, want in zip(got, expected[field]):
            if not close(item.get("revenue"), want["revenue"]):
                problems.append(f"{field}[{want[key]}] revenue {item.get('revenue')!r} != {want['revenue']}")
    return problems


class DatavizVerifier(Verifier):
    app_id = "dataviz"
    ready_path = "/"

    def run(self) -> None:
        rows = load_rows(Path(self.inputs.get("dataset", DATASET)))

        with self.check("dashboard", "GET / serves the dashboard as HTML"):
            response = self.get("/")
            expect_status(response, 200)
            expect_html(response)

        for check_id, params in QUERIES.items():
            label = ", ".join(f"{k}={v}" for k, v in params.items()) or "no filters"
            with self.check(check_id, f"GET /api/summary ({label}) matches the dataset"):
                response = self.get("/api/summary", params=params)
                expect_status(response, 200)
                problems = compare(expect_json(response), expected_summary(rows, params))
                if problems:
                    raise CheckFailed("; ".join(problems[:4]))

        with self.check("browser_chart", "The dashboard renders a chart (SVG or canvas) in a browser") as check:
            self.require_browser(check)
            with self.browser.page() as (page, errors):
                page.goto(self.base_url + "/", wait_until="networkidle")
                charts = self._wait_for_charts(page)
                expect(charts >= 1, "no chart larger than 200x100 px appeared within 30 s")

        with self.check("browser_two_charts", "The dashboard shows at least two charts", required=False) as check:
            self.require_browser(check)
            with self.browser.page() as (page, errors):
                page.goto(self.base_url + "/", wait_until="networkidle")
                charts = self._wait_for_charts(page, minimum=2)
                expect(charts >= 2, f"found {charts} chart(s)")
                expect(not errors, f"uncaught error: {errors[0][:200] if errors else ''}")

        with self.check("browser_filters", "The dashboard has filter controls", required=False) as check:
            self.require_browser(check)
            with self.browser.page() as (page, _):
                page.goto(self.base_url + "/", wait_until="networkidle")
                controls = page.locator("select, input, [role=combobox], [role=listbox]").count()
                expect(controls >= 2, f"found {controls} filter control(s)")

    @staticmethod
    def _wait_for_charts(page, minimum: int = 1) -> int:
        try:
            page.wait_for_function(f"(minimum) => ({COUNT_CHARTS})() >= minimum", arg=minimum, timeout=30_000)
        except Exception:
            pass
        return page.evaluate(COUNT_CHARTS)


# Large, outermost SVG or canvas elements; nested SVGs belong to the chart that contains them.
COUNT_CHARTS = """() => [...document.querySelectorAll('svg, canvas')].filter(e => {
    if (e.parentElement && e.parentElement.closest('svg')) return false;
    const r = e.getBoundingClientRect();
    return r.width >= 200 && r.height >= 100;
}).length"""
