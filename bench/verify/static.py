from __future__ import annotations

from bench.verify.base import CheckFailed, Verifier, expect, expect_html, expect_json, expect_status, token

PAGES = {"/": "Home", "/about": "About", "/contact": "Contact"}
CONTACT_FIELDS = {"name", "email", "message"}


class StaticSiteVerifier(Verifier):
    app_id = "static"
    ready_path = "/"

    def run(self) -> None:
        scans = {}
        for path, label in PAGES.items():
            with self.check(f"page_{label.lower()}", f"GET {path} returns HTML"):
                response = self.get(path)
                expect_status(response, 200)
                expect_html(response)
                scans[path] = self.page(path, response)

        with self.check("home_content", "Home has an <h1> containing 'Northwind Robotics'"):
            scan = self.depends_on(scans.get("/"), "page_home")
            expect(scan.heading_with("Northwind Robotics", "h1"), f"no <h1> with the company name; h1s: {_h1s(scan)}")

        with self.check("about_content", "About has a heading containing 'About'"):
            scan = self.depends_on(scans.get("/about"), "page_about")
            expect(scan.heading_with("About"), f"no heading containing 'About'; headings: {scan.headings[:5]}")

        with self.check("contact_form", "Contact has a form with name, email and message fields"):
            scan = self.depends_on(scans.get("/contact"), "page_contact")
            missing = CONTACT_FIELDS - scan.field_names
            expect(scan.forms and not missing, f"form missing fields {sorted(missing)} (found {sorted(scan.field_names)})")

        with self.check("head_tags", "Every page has a <title> and a viewport meta tag", required=False):
            bad = [p for p, s in scans.items() if not (s.title and s.has_viewport)]
            expect(scans and not bad, f"missing <title> or viewport on {bad or list(PAGES)}")

        with self.check("navigation", "Home links to /about and /contact", required=False):
            scan = self.depends_on(scans.get("/"), "page_home")
            links = [link.rstrip("/").split("?")[0] for link in scan.links]
            missing = [p for p in ("about", "contact") if not any(link.endswith(p) for link in links)]
            expect(not missing, f"no links to {missing}")

        with self.check("contact_api_valid", "POST /api/contact with valid input returns {ok: true}"):
            response = self.post(
                "/api/contact",
                json={"name": "Ada Lovelace", "email": "ada@example.com", "message": "Benchmark message " + token()},
            )
            expect_status(response, 200)
            expect(expect_json(response).get("ok") is True, f"expected ok=true, got {response.text[:200]}")

        with self.check("contact_api_validation", "POST /api/contact rejects a bad email and an empty message with 400"):
            cases = {
                "invalid email": {"name": "Ada", "email": "not-an-email", "message": "Hello"},
                "empty message": {"name": "Ada", "email": "ada@example.com", "message": ""},
            }
            for case, body in cases.items():
                response = self.post("/api/contact", json=body)
                if response.status_code != 400:
                    raise CheckFailed(f"{case}: expected 400, got {response.status_code}")
                expect(expect_json(response).get("ok") is False, f"{case}: expected ok=false")

        with self.check("not_found", "Unknown paths return 404"):
            expect_status(self.get("/no-such-page-" + token()), 404)

        self.screenshot("/", "home", "The home page")

        with self.check("browser_contact_form", "Submitting the /contact form in a browser posts to /api/contact without leaving the page") as check:
            self.require_browser(check)
            self._submit_contact_form()

        with self.check("browser_no_errors", "Pages load in a browser without uncaught JavaScript errors", required=False) as check:
            self.require_browser(check)
            for path in PAGES:
                with self.browser.page() as (page, errors):
                    page.goto(self.base_url + path, wait_until="networkidle")
                    expect(not errors, f"{path}: {errors[0][:200] if errors else ''}")

    def _submit_contact_form(self) -> None:
        with self.browser.page() as (page, _):
            page.goto(self.base_url + "/contact", wait_until="networkidle")
            form = page.locator("form").filter(has=page.locator("[name=email]")).first
            form.locator("[name=name]").first.fill("Grace Hopper")
            form.locator("[name=email]").first.fill("grace@example.com")
            form.locator("[name=message]").first.fill("Hello from the benchmark " + token())
            # A full reload or navigation wipes this marker; an in-page fetch keeps it.
            page.evaluate("() => { window.__benchMarker = 42 }")
            submit = form.locator("button[type=submit], input[type=submit], button:not([type])").first
            with page.expect_response(
                lambda r: "/api/contact" in r.url and r.request.method == "POST", timeout=20_000
            ) as info:
                submit.click()
            response = info.value
            expect(response.status == 200, f"browser submission got HTTP {response.status}")
            page.wait_for_timeout(1500)
            self.capture(page, "contact", "The contact page after the verifier submitted the form")
            try:
                marker = page.evaluate("() => window.__benchMarker")
            except Exception:  # the execution context was destroyed by a navigation
                marker = None
            expect(marker == 42, f"the page reloaded or navigated to {page.url} after submitting")


def _h1s(scan) -> list[str]:
    return [text for tag, text in scan.headings if tag == "h1"][:3]
