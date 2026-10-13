from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import Any, Callable
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx

from bench.verify.base import (
    USER_AGENT, CheckFailed, Verifier, expect, expect_html, expect_json, expect_status, no_cookies, token,
)

Predicate = Callable[[dict], bool]


class Client:
    """One chat participant; records every `message` event it receives with a timestamp."""

    def __init__(self, room: str, user: str) -> None:
        self.room, self.user = room, user
        self.inbox: list[tuple[float, dict]] = []
        self._reader: asyncio.Task | None = None

    def ingest(self, raw: str | bytes) -> None:
        try:
            payload = json.loads(raw)
        except ValueError:
            return
        for item in payload if isinstance(payload, list) else [payload]:
            if isinstance(item, dict) and item.get("type", "message") == "message" and "text" in item:
                self.inbox.append((time.monotonic(), item))

    def find(self, predicate: Predicate) -> tuple[float, dict] | None:
        return next(((t, m) for t, m in self.inbox if predicate(m)), None)

    async def wait_for(self, predicate: Predicate, timeout: float) -> tuple[float, dict] | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = self.find(predicate)
            if found:
                return found
            await asyncio.sleep(0.05)
        return self.find(predicate)

    async def close(self) -> None:
        if self._reader:
            self._reader.cancel()
            with contextlib.suppress(BaseException):
                await self._reader


class WebSocketClient(Client):
    def __init__(self, url: str, room: str, user: str) -> None:
        super().__init__(room, user)
        self.url = url
        self.ws: Any = None

    async def connect(self) -> None:
        from websockets.asyncio.client import connect

        separator = "&" if "?" in self.url else "?"
        target = f"{self.url}{separator}{urlencode({'room': self.room, 'user': self.user})}"
        self.ws = await connect(target, open_timeout=60, user_agent_header=USER_AGENT)
        self._reader = asyncio.create_task(self._read())

    async def _read(self) -> None:
        with contextlib.suppress(Exception):
            async for raw in self.ws:
                self.ingest(raw)

    async def send(self, text: str) -> None:
        await self.ws.send(json.dumps({"type": "message", "text": text}))

    async def close(self) -> None:
        await super().close()
        if self.ws is not None:
            with contextlib.suppress(Exception):
                await self.ws.close()


class SSEClient(Client):
    def __init__(self, http: httpx.AsyncClient, room: str, user: str) -> None:
        super().__init__(room, user)
        self.http = http
        self._stream: Any = None

    async def connect(self) -> None:
        self._stream = self.http.stream(
            "GET",
            f"/api/rooms/{self.room}/events",
            headers={"Accept": "text/event-stream"},
            timeout=httpx.Timeout(60.0, read=None),
        )
        response = await self._stream.__aenter__()
        expect_status(response, 200)
        self._reader = asyncio.create_task(self._read(response))

    async def _read(self, response: httpx.Response) -> None:
        data: list[str] = []
        with contextlib.suppress(Exception):
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data.append(line[5:].lstrip())
                elif not line.strip() and data:
                    self.ingest("\n".join(data))
                    data = []

    async def send(self, text: str) -> None:
        response = await self.http.post(f"/api/rooms/{self.room}/messages", json={"user": self.user, "text": text})
        expect_status(response, 201, 200)

    async def close(self) -> None:
        await super().close()
        if self._stream is not None:
            with contextlib.suppress(Exception):
                await self._stream.__aexit__(None, None, None)


NAME_FIELDS = ", ".join(f"{selector}:visible" for selector in (
    "input[placeholder*=name i]", "input[name*=name i]", "input[id*=name i]", "input[aria-label*=name i]",
    "input[placeholder*=nick i]"))


def shows(page: Any, text: str, wait_ms: int) -> bool:
    try:
        page.wait_for_function("(text) => document.body && document.body.innerText.includes(text)", arg=text,
                               timeout=wait_ms)
        return True
    except Exception:
        return False


def websocket_url(base_url: str) -> str:
    parts = urlsplit(base_url)
    scheme = {"https": "wss", "http": "ws"}.get(parts.scheme, parts.scheme)
    return urlunsplit((scheme, parts.netloc, parts.path.rstrip("/") + "/ws", "", ""))


class RealtimeVerifier(Verifier):
    app_id = "realtime"
    ready_path = "/"

    def run(self) -> None:
        realtime = self.deployment.get("realtime") or {}
        self.transport = str(realtime.get("transport") or "websocket").lower()
        self.ws_url = realtime.get("url") or websocket_url(self.base_url)
        self.latency_ms: float | None = None
        self.chat: tuple[str, str] | None = None  # (room, a message sent there), once the live checks ran

        with self.check("ui", "GET / serves the chat UI as HTML"):
            response = self.get("/")
            expect_status(response, 200)
            expect_html(response)

        with self.check("transport", "deployment.json declares a supported transport (websocket or sse)", required=False):
            expect(self.transport in ("websocket", "sse"), f"unknown transport {self.transport!r}")

        run_id = token()
        self.run_async(lambda: self._live_checks(run_id))

        with self.check("browser_ui", "The chat UI loads in a browser without errors", required=False) as check:
            self.require_browser(check)
            with self.browser.page() as (page, errors):
                page.goto(self.base_url + "/?room=bench-ui", wait_until="networkidle")
                expect(page.locator("input, textarea").count() > 0, "no input for typing messages")
                expect(not errors, f"uncaught error: {errors[0][:200] if errors else ''}")
        if self.chat:
            self._capture_room(*self.chat)

    def _capture_room(self, room: str, text: str) -> None:
        """Opens the room the verifier's clients chatted in, so the screenshot shows its history. A UI
        that first asks for a display name gets one."""
        if not self.can_capture():
            return
        with contextlib.suppress(Exception), self.browser.page() as (page, _):
            page.set_default_timeout(10_000)
            page.goto(f"{self.base_url}/?{urlencode({'room': room})}", wait_until="networkidle")
            shown = shows(page, text, wait_ms=3000)
            name = page.locator(NAME_FIELDS).first
            if not shown and name.count():
                name.fill("visitor")
                name.press("Enter")
                shown = shows(page, text, wait_ms=5000)
            self.capture(page, "chat", "The room the verifier's clients chatted in, with its history" if shown
                         else "The chat UI, opened on the room the verifier's clients chatted in")

    async def _live_checks(self, run_id: str) -> None:
        http = httpx.AsyncClient(base_url=self.base_url, timeout=30.0, headers={"User-Agent": USER_AGENT},
                                 cookies=no_cookies())  # the simulated users share this client
        clients: list[Client] = []

        def make(room: str, user: str) -> Client:
            client = SSEClient(http, room, user) if self.transport == "sse" else WebSocketClient(self.ws_url, room, user)
            clients.append(client)
            return client

        room, other_room, crowd_room = f"bench-{run_id}", f"bench-{run_id}-other", f"bench-{run_id}-crowd"
        text = f"hello from alice {run_id}"
        self.chat = (room, text)
        alice = bob = carol = None
        try:
            with self.check("connect", f"Clients connect over {self.transport}"):
                alice, bob, carol = make(room, "alice"), make(room, "bob"), make(other_room, "carol")
                await asyncio.wait_for(asyncio.gather(alice.connect(), bob.connect(), carol.connect()), 90)
                await asyncio.sleep(1.5)  # let the server register subscribers before anyone posts

            with self.check("delivery", "A message reaches another client in the same room within 5 s"):
                self.depends_on(self.passed("connect") or None, "connect")
                sent = time.monotonic()
                await alice.send(text)
                found = await bob.wait_for(lambda m: m.get("text") == text, 5)
                expect(found, "bob did not receive alice's message within 5 s")
                received_at, message = found
                self.latency_ms = round((received_at - sent) * 1000)
                expect(message.get("user") == "alice", f"message user is {message.get('user')!r}, expected 'alice'")

            with self.check("echo", "The sender receives its own message too", required=False):
                self.depends_on(self.passed("connect") or None, "connect")
                expect(await alice.wait_for(lambda m: m.get("text") == text, 3), "alice did not get her own message")

            with self.check("room_isolation", "Messages never reach clients in other rooms"):
                self.depends_on(self.passed("delivery") or None, "delivery")
                await asyncio.sleep(2)
                expect(not carol.find(lambda m: m.get("text") == text), "a client in another room received the message")

            with self.check("fanout", "Five users posting at the same time all see every message within 10 s"):
                crowd = [make(crowd_room, f"user{i}") for i in range(5)]
                await asyncio.wait_for(asyncio.gather(*(c.connect() for c in crowd)), 90)
                await asyncio.sleep(1.5)
                texts = {c.user: [f"{c.user} says {n} {run_id}" for n in range(3)] for c in crowd}

                async def post_all(client: Client) -> None:
                    for message in texts[client.user]:
                        await client.send(message)

                await asyncio.gather(*(post_all(c) for c in crowd))
                deadline = time.monotonic() + 10
                missing: dict[str, int] = {}
                for client in crowd:
                    expected = {t for user, ts in texts.items() if user != client.user for t in ts}
                    while time.monotonic() < deadline and not expected <= self._texts(client):
                        await asyncio.sleep(0.1)
                    if lost := len(expected - self._texts(client)):
                        missing[client.user] = lost
                expect(not missing, f"messages not delivered (client: missing count): {missing}")

            with self.check("history", "GET /api/rooms/<room>/messages returns recent messages"):
                response = await http.get(f"/api/rooms/{room}/messages")
                expect_status(response, 200)
                history = expect_json(response)
                expect(isinstance(history, list), f"expected a JSON array, got {response.text[:200]}")
                if self.passed("delivery"):
                    entry = next((m for m in history if isinstance(m, dict) and m.get("text") == text), None)
                    expect(entry and entry.get("user") == "alice", "alice's message is missing from the history")

            with self.check("validation", "Messages over 1000 characters are rejected", required=False):
                too_long = "x" * 1001 + run_id
                if self.transport == "sse":
                    response = await http.post(f"/api/rooms/{room}/messages", json={"user": "alice", "text": too_long})
                    if response.status_code not in (400, 413, 422):
                        raise CheckFailed(f"expected 400, got {response.status_code}")
                else:
                    self.depends_on(self.passed("connect") or None, "connect")
                    await alice.send(too_long)
                    await asyncio.sleep(2)
                    expect(not bob.find(lambda m: m.get("text") == too_long), "an over-long message was broadcast")
        finally:
            await asyncio.gather(*(c.close() for c in clients), return_exceptions=True)
            await http.aclose()

    @staticmethod
    def _texts(client: Client) -> set[str]:
        return {m.get("text") for _, m in client.inbox}

    def run_all(self) -> dict[str, Any]:
        result = super().run_all()
        result["performance"]["delivery_latency_ms"] = getattr(self, "latency_ms", None)
        return result
