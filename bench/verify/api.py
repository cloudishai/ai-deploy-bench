from __future__ import annotations

import time

from bench.verify.base import CheckFailed, Verifier, expect, expect_html, expect_json, expect_status, token

# A fixed one-minute window can split a burst in two, so send more than twice the limit.
RATE_LIMIT_BURST = 130


class ApiVerifier(Verifier):
    app_id = "api"
    ready_path = "/health"

    def run(self) -> None:
        keys = self.inputs.get("api_keys") or []
        if len(keys) < 2:
            raise CheckFailed("verifier needs two API keys in inputs.api_keys")
        key_a, key_b = keys[0], keys[1]
        tag = "t-" + token()
        first = second = None
        created_at = None

        with self.check("health", "GET /health returns {status: ok}"):
            response = self.get("/health")
            expect_status(response, 200)
            expect(expect_json(response).get("status") == "ok", f"unexpected body {response.text[:200]}")

        with self.check("openapi", "GET /openapi.json is an OpenAPI 3 document covering /v1/notes"):
            response = self.get("/openapi.json")
            expect_status(response, 200)
            doc = expect_json(response)
            expect(str(doc.get("openapi", "")).startswith("3"), f"openapi version is {doc.get('openapi')!r}")
            paths = list((doc.get("paths") or {}).keys())
            expect(any(p.startswith("/v1/notes") for p in paths), f"paths don't include /v1/notes: {paths[:10]}")

        with self.check("docs", "GET /docs serves human-readable documentation", required=False):
            response = self.get("/docs")
            expect_status(response, 200)
            expect_html(response)

        with self.check("auth_missing", "Requests without an API key get 401"):
            expect_status(self.get("/v1/notes"), 401, 403)

        with self.check("auth_invalid", "Requests with an unknown API key get 401"):
            expect_status(self.get("/v1/notes", headers=self._key("invalid-" + token())), 401, 403)

        with self.check("create", "POST /v1/notes creates a note"):
            first = self._create(key_a, {"title": "First " + tag, "content": "Hello", "tags": ["bench", tag]})
            second = self._create(key_a, {"title": "Second " + tag, "content": "World", "tags": ["bench"]})
            created_at = time.monotonic()

        with self.check("create_validation", "Invalid notes are rejected with 400"):
            for case, body in {"missing title": {"content": "x"}, "wrong type": {"title": 123, "content": "x"}}.items():
                response = self.post("/v1/notes", json=body, headers=self._key(key_a))
                if response.status_code not in (400, 422):
                    raise CheckFailed(f"{case}: expected 400, got {response.status_code}")

        with self.check("get", "GET /v1/notes/{id} returns the note"):
            self.depends_on(first, "create")
            response = self.get(f"/v1/notes/{first['id']}", headers=self._key(key_a))
            expect_status(response, 200)
            expect(expect_json(response).get("title") == first["title"], "title mismatch")

        with self.check("list", "GET /v1/notes lists notes and filters by tag"):
            self.depends_on(first, "create")
            ids = self._list_ids(key_a)
            expect(str(first["id"]) in ids and str(second["id"]) in ids, f"created notes missing from {ids[:10]}")
            expect(self._list_ids(key_a, tag) == [str(first["id"])], "tag filter returned the wrong notes")

        with self.check("list_order", "Notes are listed newest first", required=False):
            self.depends_on(first, "create")
            ids = self._list_ids(key_a)
            expect(ids.index(str(second["id"])) < ids.index(str(first["id"])), "not newest first")

        with self.check("update", "PATCH /v1/notes/{id} updates only the given fields"):
            self.depends_on(first, "create")
            response = self.patch(f"/v1/notes/{first['id']}", json={"title": "Renamed " + tag}, headers=self._key(key_a))
            expect_status(response, 200)
            note = expect_json(response)
            expect(note.get("title") == "Renamed " + tag, f"title not updated: {note.get('title')!r}")
            expect(note.get("content") == "Hello", f"content changed to {note.get('content')!r}")

        with self.check("isolation", "Notes are private to the API key that created them"):
            self.depends_on(first, "create")
            path = f"/v1/notes/{first['id']}"
            expect_status(self.get(path, headers=self._key(key_b)), 404, 403)
            expect(str(first["id"]) not in self._list_ids(key_b), "key B can list key A's note")
            expect_status(self.patch(path, json={"title": "hijacked"}, headers=self._key(key_b)), 404, 403)
            expect_status(self.delete(path, headers=self._key(key_b)), 404, 403)

        with self.check("delete", "DELETE /v1/notes/{id} removes the note"):
            self.depends_on(second, "create")
            path = f"/v1/notes/{second['id']}"
            expect_status(self.delete(path, headers=self._key(key_a)), 204, 200)
            expect_status(self.get(path, headers=self._key(key_a)), 404)

        with self.check("persistence", "Notes are still there a minute later"):
            self.depends_on(first, "create")
            self.sleep_until_persistence_window(created_at)
            expect_status(self.get(f"/v1/notes/{first['id']}", headers=self._key(key_a)), 200)

        limited = None
        with self.check("rate_limit", "Exceeding 60 requests/minute returns 429"):
            limited = self._burst(key_b)
            expect(limited is not None, f"no 429 after {RATE_LIMIT_BURST} requests in a burst")

        with self.check("rate_limit_retry_after", "429 responses include a Retry-After header", required=False):
            self.depends_on(limited, "rate_limit")
            expect(limited.headers.get("retry-after"), "no Retry-After header")

        with self.check("rate_limit_per_key", "One key hitting its limit doesn't throttle other keys"):
            self.depends_on(limited, "rate_limit")
            expect_status(self.get("/v1/notes", headers=self._key(key_a)), 200)

    @staticmethod
    def _key(value: str) -> dict[str, str]:
        return {"X-API-Key": value}

    def _create(self, key: str, body: dict) -> dict:
        response = self.post("/v1/notes", json=body, headers=self._key(key))
        expect_status(response, 201, 200)
        note = expect_json(response)
        expect(isinstance(note, dict) and "id" in note, f"no id in {response.text[:200]}")
        expect(note.get("title") == body["title"], f"title mismatch: {note.get('title')!r}")
        expect(sorted(note.get("tags") or []) == sorted(body.get("tags") or []), f"tags mismatch: {note.get('tags')!r}")
        return note

    def _list_ids(self, key: str, tag: str | None = None) -> list[str]:
        response = self.get("/v1/notes", params={"tag": tag} if tag else None, headers=self._key(key))
        expect_status(response, 200)
        data = expect_json(response)
        notes = data.get("data") if isinstance(data, dict) else None
        expect(isinstance(notes, list), f"expected {{\"data\": [...]}}, got {response.text[:200]}")
        return [str(n.get("id")) for n in notes]

    def _burst(self, key: str):
        for _ in range(RATE_LIMIT_BURST):
            response = self.get("/v1/notes", headers=self._key(key))  # stops at the time budget
            if response.status_code == 429:
                return response
        return None
