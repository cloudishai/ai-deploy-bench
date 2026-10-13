from __future__ import annotations

import time

from bench.verify.base import CheckFailed, Verifier, expect, expect_html, expect_json, expect_status, token

PASSWORD = "correct-horse-battery-staple"


def bearer(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def same_id(a, b) -> bool:
    return str(a) == str(b)


class CrudVerifier(Verifier):
    app_id = "crud"
    ready_path = "/"

    def run(self) -> None:
        run_id = token()
        email_a, email_b = f"bench-a-{run_id}@example.com", f"bench-b-{run_id}@example.com"
        token_a = token_b = None
        first = second = None
        created_at = None

        with self.check("ui", "GET / serves the web app as HTML"):
            response = self.get("/")
            expect_status(response, 200)
            expect_html(response)

        with self.check("signup", "POST /api/auth/signup creates an account and returns a token"):
            token_a = self._signup(email_a)

        with self.check("signup_validation", "Signup rejects an invalid email and a short password with 400"):
            for case, body in {
                "invalid email": {"email": "not-an-email", "password": PASSWORD},
                "short password": {"email": f"bench-short-{run_id}@example.com", "password": "short"},
            }.items():
                response = self.post("/api/auth/signup", json=body)
                if response.status_code not in (400, 422):
                    raise CheckFailed(f"{case}: expected 400, got {response.status_code}")

        with self.check("signup_duplicate", "Signing up twice with the same email returns 409"):
            self.depends_on(token_a, "signup")
            expect_status(self.post("/api/auth/signup", json={"email": email_a, "password": PASSWORD}), 409, 400, 422)

        with self.check("login", "POST /api/auth/login returns a token"):
            self.depends_on(token_a, "signup")
            token_a = self._login(email_a)

        with self.check("login_wrong_password", "Login with a wrong password returns 401"):
            self.depends_on(token_a, "signup")
            expect_status(self.post("/api/auth/login", json={"email": email_a, "password": "wrong-" + PASSWORD}), 401, 400, 403)

        with self.check("auth_required", "/api/todos requires a valid token (401)"):
            expect_status(self.get("/api/todos"), 401, 403)
            expect_status(self.get("/api/todos", headers=bearer("not-a-real-token")), 401, 403)

        with self.check("create", "POST /api/todos creates a todo"):
            self.depends_on(token_a, "login")
            first = self._create(token_a, "Buy milk " + run_id)
            second = self._create(token_a, "Walk the dog " + run_id)
            created_at = time.monotonic()

        with self.check("create_validation", "An empty title is rejected with 400"):
            self.depends_on(token_a, "login")
            expect_status(self.post("/api/todos", json={"title": ""}, headers=bearer(token_a)), 400, 422)

        with self.check("list", "GET /api/todos lists the caller's todos"):
            self.depends_on(first, "create")
            ids = [str(t.get("id")) for t in self._list(token_a)]
            expect(str(first["id"]) in ids and str(second["id"]) in ids, f"created todos missing from {ids}")

        with self.check("list_order", "Todos are listed oldest first", required=False):
            self.depends_on(first, "create")
            ids = [str(t.get("id")) for t in self._list(token_a)]
            expect(ids.index(str(first["id"])) < ids.index(str(second["id"])), f"unexpected order {ids}")

        with self.check("update", "PATCH /api/todos/{id} renames and completes a todo"):
            self.depends_on(first, "create")
            response = self.patch(f"/api/todos/{first['id']}", json={"completed": True}, headers=bearer(token_a))
            expect_status(response, 200)
            expect(expect_json(response).get("completed") is True, f"completed not true: {response.text[:200]}")
            new_title = "Buy oat milk " + run_id
            response = self.patch(f"/api/todos/{first['id']}", json={"title": new_title}, headers=bearer(token_a))
            expect_status(response, 200)
            stored = self._find(token_a, first["id"])
            expect(stored and stored.get("title") == new_title and stored.get("completed") is True, f"update not persisted: {stored}")

        with self.check("isolation", "Users can't see or modify each other's todos (404)"):
            self.depends_on(first, "create")
            token_b = self._signup(email_b)
            expect(self._find(token_b, first["id"]) is None, "user B can see user A's todo")
            expect_status(self.patch(f"/api/todos/{first['id']}", json={"title": "hijacked"}, headers=bearer(token_b)), 404, 403)
            expect_status(self.delete(f"/api/todos/{first['id']}", headers=bearer(token_b)), 404, 403)
            stored = self._find(token_a, first["id"])
            expect(stored and stored.get("title") != "hijacked", "user B modified user A's todo")

        with self.check("delete", "DELETE /api/todos/{id} removes a todo"):
            self.depends_on(second, "create")
            expect_status(self.delete(f"/api/todos/{second['id']}", headers=bearer(token_a)), 204, 200)
            expect(self._find(token_a, second["id"]) is None, "deleted todo is still listed")
            expect_status(self.delete(f"/api/todos/{second['id']}", headers=bearer(token_a)), 404)

        with self.check("persistence", "Data is still there a minute later, with a fresh login"):
            self.depends_on(first, "create")
            self.sleep_until_persistence_window(created_at)
            fresh = self._login(email_a)
            stored = self._find(fresh, first["id"])
            expect(stored and stored.get("completed") is True, f"todo lost or changed: {stored}")

        with self.check("browser_ui", "The web UI renders a login or signup form", required=False) as check:
            self.require_browser(check)
            with self.browser.page() as (page, errors):
                page.goto(self.base_url + "/", wait_until="networkidle")
                expect(page.locator("input[type=password]").count() > 0, "no password field on /")
                expect(not errors, f"uncaught error: {errors[0][:200] if errors else ''}")

    def _signup(self, email: str) -> str:
        response = self.post("/api/auth/signup", json={"email": email, "password": PASSWORD})
        expect_status(response, 201, 200)
        return self._token(response)

    def _login(self, email: str) -> str:
        response = self.post("/api/auth/login", json={"email": email, "password": PASSWORD})
        expect_status(response, 200)
        return self._token(response)

    @staticmethod
    def _token(response) -> str:
        value = expect_json(response).get("token")
        expect(isinstance(value, str) and value, f"response has no token: {response.text[:200]}")
        return value

    def _create(self, auth: str, title: str) -> dict:
        response = self.post("/api/todos", json={"title": title}, headers=bearer(auth))
        expect_status(response, 201, 200)
        todo = expect_json(response)
        expect(isinstance(todo, dict) and "id" in todo, f"no id in {response.text[:200]}")
        expect(todo.get("title") == title, f"title mismatch: {todo.get('title')!r}")
        expect(todo.get("completed") is False, f"new todo has completed={todo.get('completed')!r}")
        return todo

    def _list(self, auth: str) -> list[dict]:
        response = self.get("/api/todos", headers=bearer(auth))
        expect_status(response, 200)
        todos = expect_json(response)
        expect(isinstance(todos, list), f"expected a JSON array, got {type(todos).__name__}")
        return todos

    def _find(self, auth: str, todo_id) -> dict | None:
        return next((t for t in self._list(auth) if same_id(t.get("id"), todo_id)), None)
