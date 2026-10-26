"""Minimal reference implementations of the five benchmark apps, used to test the verifiers.

Each factory takes a set of `bugs` to switch off one behavior, so tests can prove that a verifier
catches it.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import json
import re
import secrets
import socket
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from aiohttp import WSMsgType, web

SALES_CSV = Path(__file__).resolve().parents[1] / "apps" / "dataviz" / "fixtures" / "data" / "sales.csv"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
API_KEY = web.RequestKey("api_key", str)


def page(title: str, body: str, script: str = "") -> web.Response:
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title></head>
<body><nav><a href="/">Home</a> <a href="/about">About</a> <a href="/contact">Contact</a></nav>
{body}<script>{script}</script></body></html>"""
    return web.Response(text=html, content_type="text/html")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def error(status: int, message: str, **extra) -> web.Response:
    return web.json_response({"error": message, **extra}, status=status)


async def json_body(request: web.Request) -> dict:
    try:
        body = await request.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


# -- static ----------------------------------------------------------------------------------

CONTACT_SCRIPT = """
document.querySelector('form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const response = await fetch('/api/contact', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(Object.fromEntries(form))});
  document.querySelector('#status').textContent = response.ok ? 'Thanks!' : 'Something went wrong';
});"""


SPA_SHELL = """<!doctype html><html><head><meta name="viewport" content="width=device-width"><title>Northwind</title>
</head><body><div id="root"></div><script>
const pages = {"/": "<h1>Northwind Robotics</h1>", "/about": "<h2>About Northwind</h2>"};
document.getElementById("root").innerHTML = pages[location.pathname] || "";
</script></body></html>"""


def static_app(bugs: frozenset = frozenset()) -> web.Application:
    """`bugs` may also contain "spa": the home and about pages render client-side."""

    async def home(_):
        if "spa" in bugs:
            return web.Response(text=SPA_SHELL, content_type="text/html")
        return page("Northwind Robotics", "<h1>Northwind Robotics</h1><p>Robot arms for small factories.</p>")

    async def about(_):
        if "spa" in bugs:
            return web.Response(text=SPA_SHELL, content_type="text/html")
        return page("About", "<h2>About Northwind</h2><p>Founded in 2019.</p>")

    async def contact(_):
        form = """<h2>Contact</h2><form method="post" action="/api/contact"><input name="name"><input name="email">
<textarea name="message"></textarea><button type="submit">Send</button></form><p id="status"></p>"""
        return page("Contact", form, "" if "full_reload" in bugs else CONTACT_SCRIPT)

    async def submit(request):
        body = await json_body(request)
        if "no_validation" not in bugs:
            if not body.get("name") or not EMAIL.match(str(body.get("email", ""))) or not body.get("message"):
                return web.json_response({"ok": False, "error": "invalid input"}, status=400)
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_get("/", home)
    app.router.add_get("/about", about)
    app.router.add_get("/contact", contact)
    if "no_contact_api" not in bugs:
        app.router.add_post("/api/contact", submit)
    return app


# -- crud ------------------------------------------------------------------------------------

# Signs in and lists the user's todos, so the verifier's screenshot of the signed-in UI can be tested.
TODO_SCRIPT = """
document.querySelector('form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const login = await fetch('/api/auth/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: form.get('email'), password: form.get('password')})});
  if (!login.ok) return;
  const {token} = await login.json();
  const todos = await (await fetch('/api/todos', {headers: {Authorization: 'Bearer ' + token}})).json();
  document.querySelector('#todos').replaceChildren(...todos.map(todo => {
    const item = document.createElement('li');
    item.textContent = todo.title;
    return item;
  }));
});
"""

def crud_app(bugs: frozenset = frozenset()) -> web.Application:
    """`bugs` may also contain "cookie_sessions": signup and login also set a session cookie, which
    the API accepts when there's no Authorization header (TASK.md lets the web UI use cookies).
    "no_ui_login" leaves the web UI's form without the script that signs in."""
    users: dict[str, str] = {}
    tokens: dict[str, str] = {}
    todos: list[dict] = []
    counter = iter(range(1, 10**9))

    def hash_password(password: str) -> str:
        return hashlib.scrypt(password.encode(), salt=b"bench", n=2**10, r=8, p=1).hex()

    def issue(email: str) -> str:
        value = secrets.token_urlsafe(16)
        tokens[value] = email
        return value

    def session(email: str, status: int = 200) -> web.Response:
        token = issue(email)
        response = web.json_response({"token": token}, status=status)
        if "cookie_sessions" in bugs:
            response.set_cookie("token", token, httponly=True, samesite="Lax")
        return response

    def caller(request) -> str | None:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            return tokens.get(header.removeprefix("Bearer ").strip())
        return tokens.get(request.cookies.get("token", "")) if "cookie_sessions" in bugs else None

    def visible(email: str) -> list[dict]:
        return todos if "no_isolation" in bugs else [t for t in todos if t["owner"] == email]

    def public(todo: dict) -> dict:
        return {k: v for k, v in todo.items() if k != "owner"}

    async def ui(_):
        return page("Todos", "<h1>Todos</h1><form><input name='email'><input type='password' name='password'>"
                    "<button type='submit'>Log in</button></form><ul id='todos'></ul>",
                    "" if "no_ui_login" in bugs else TODO_SCRIPT)

    async def signup(request):
        body = await json_body(request)
        email, password = str(body.get("email", "")), str(body.get("password", ""))
        if not EMAIL.match(email) or len(password) < 8:
            return error(400, "invalid email or password")
        if email in users:
            return error(409, "email already registered")
        users[email] = hash_password(password)
        return session(email, 201)

    async def login(request):
        body = await json_body(request)
        email = str(body.get("email", ""))
        if users.get(email) != hash_password(str(body.get("password", ""))):
            return error(401, "wrong credentials")
        return session(email)

    async def list_todos(request):
        if not (email := caller(request)):
            return error(401, "unauthorized")
        return web.json_response([public(t) for t in visible(email)])

    async def create(request):
        if not (email := caller(request)):
            return error(401, "unauthorized")
        title = str((await json_body(request)).get("title", "")).strip()
        if not title:
            return error(400, "title required")
        todo = {"id": next(counter), "title": title, "completed": False, "created_at": now(), "owner": email}
        todos.append(todo)
        return web.json_response(public(todo), status=201)

    def owned(request, email):
        todo_id = request.match_info["id"]
        return next((t for t in visible(email) if str(t["id"]) == todo_id), None)

    async def update(request):
        if not (email := caller(request)):
            return error(401, "unauthorized")
        if not (todo := owned(request, email)):
            return error(404, "not found")
        body = await json_body(request)
        for field in ("title", "completed"):
            if field in body:
                todo[field] = body[field]
        return web.json_response(public(todo))

    async def remove(request):
        if not (email := caller(request)):
            return error(401, "unauthorized")
        if not (todo := owned(request, email)):
            return error(404, "not found")
        todos.remove(todo)
        return web.Response(status=204)

    app = web.Application()
    app.router.add_get("/", ui)
    app.router.add_post("/api/auth/signup", signup)
    app.router.add_post("/api/auth/login", login)
    app.router.add_get("/api/todos", list_todos)
    app.router.add_post("/api/todos", create)
    app.router.add_patch("/api/todos/{id}", update)
    app.router.add_delete("/api/todos/{id}", remove)
    return app


# -- api -------------------------------------------------------------------------------------

OPENAPI = {
    "openapi": "3.1.0",
    "info": {"title": "Notes API", "version": "1.0.0"},
    "paths": {"/v1/notes": {"get": {}, "post": {}}, "/v1/notes/{id}": {"get": {}, "patch": {}, "delete": {}}},
}


def api_app(keys: list[str], bugs: frozenset = frozenset(), window_s: float = 60) -> web.Application:
    notes: list[dict] = []
    hits: dict[str, deque] = defaultdict(deque)

    @web.middleware
    async def auth(request, handler):
        if not request.path.startswith("/v1/"):
            return await handler(request)
        key = request.headers.get("X-API-Key")
        if key not in keys:
            return error(401, "invalid API key")
        if "no_rate_limit" not in bugs:
            window = hits["*" if "global_rate_limit" in bugs else key]
            current = time.monotonic()
            while window and current - window[0] > window_s:
                window.popleft()
            if len(window) >= 60:
                response = error(429, "rate limit exceeded")
                response.headers["Retry-After"] = str(int(window_s - (current - window[0])) + 1)
                return response
            window.append(current)
        request[API_KEY] = key
        return await handler(request)

    def valid(body: dict, partial: bool) -> bool:
        if "title" in body or not partial:
            if not isinstance(body.get("title"), str) or not body["title"].strip():
                return False
        if "content" in body and not isinstance(body["content"], str):
            return False
        return "tags" not in body or (isinstance(body["tags"], list) and all(isinstance(t, str) for t in body["tags"]))

    def mine(request) -> dict | None:
        return next((n for n in notes if n["id"] == request.match_info["id"] and n["key"] == request[API_KEY]), None)

    def public(note: dict) -> dict:
        return {k: v for k, v in note.items() if k != "key"}

    async def health(_):
        return web.json_response({"status": "ok"})

    async def openapi(_):
        return web.json_response(OPENAPI)

    async def docs(_):
        return page("Notes API docs", "<h1>Notes API</h1>")

    async def create(request):
        body = await json_body(request)
        if not valid(body, partial=False):
            return error(400, "invalid note")
        stamp = now()
        note = {"id": secrets.token_hex(6), "title": body["title"], "content": body.get("content", ""),
                "tags": body.get("tags", []), "created_at": stamp, "updated_at": stamp, "key": request[API_KEY]}
        notes.append(note)
        return web.json_response(public(note), status=201)

    async def list_notes(request):
        tag = request.query.get("tag")
        found = [n for n in notes if n["key"] == request[API_KEY] and (not tag or tag in n["tags"])]
        return web.json_response({"data": [public(n) for n in reversed(found)]})

    async def get_note(request):
        note = mine(request)
        return web.json_response(public(note)) if note else error(404, "not found")

    async def update(request):
        if not (note := mine(request)):
            return error(404, "not found")
        body = await json_body(request)
        if not valid(body, partial=True):
            return error(400, "invalid note")
        note.update({k: body[k] for k in ("title", "content", "tags") if k in body}, updated_at=now())
        return web.json_response(public(note))

    async def remove(request):
        if not (note := mine(request)):
            return error(404, "not found")
        notes.remove(note)
        return web.Response(status=204)

    app = web.Application(middlewares=[auth])
    app.router.add_get("/health", health)
    app.router.add_get("/openapi.json", openapi)
    app.router.add_get("/docs", docs)
    app.router.add_post("/v1/notes", create)
    app.router.add_get("/v1/notes", list_notes)
    app.router.add_get("/v1/notes/{id}", get_note)
    app.router.add_patch("/v1/notes/{id}", update)
    app.router.add_delete("/v1/notes/{id}", remove)
    return app


# -- dataviz ---------------------------------------------------------------------------------

DASHBOARD = """<h1>Sales</h1><select id="region"><option></option></select><select id="category"></select>
<svg width="600" height="300"><rect width="600" height="300" fill="#eee"/></svg>
<svg width="400" height="300"><rect width="400" height="300" fill="#ddd"/></svg>"""


def dataviz_app(bugs: frozenset = frozenset()) -> web.Application:
    with SALES_CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))

    async def dashboard(_):
        return page("Sales dashboard", DASHBOARD)

    async def summary(request):
        q = request.query
        cents_month: dict[str, int] = defaultdict(int)
        cents_category: dict[str, int] = defaultdict(int)
        orders = units = cents = 0
        for row in rows:
            if q.get("region") and row["region"] != q["region"]:
                continue
            if q.get("category") and row["category"] != q["category"]:
                continue
            if (q.get("start") and row["date"] < q["start"]) or (q.get("end") and row["date"] > q["end"]):
                continue
            value = round(float(row["revenue"]) * 100)
            orders, units, cents = orders + 1, units + int(row["units"]), cents + value
            cents_month[row["date"][:7]] += value
            cents_category[row["category"]] += value
        if "off_by_one" in bugs:
            orders += 1
        return web.json_response({
            "total_revenue": cents / 100,
            "orders": orders,
            "units": units,
            "revenue_by_month": [{"month": m, "revenue": c / 100} for m, c in sorted(cents_month.items())],
            "revenue_by_category": [
                {"category": k, "revenue": c / 100} for k, c in sorted(cents_category.items(), key=lambda kv: -kv[1])
            ],
        })

    app = web.Application()
    app.router.add_get("/", dashboard)
    app.router.add_get("/api/summary", summary)
    return app


# -- realtime --------------------------------------------------------------------------------

CHAT_SCRIPT = """
const room = new URLSearchParams(location.search).get('room') || 'general';
fetch('/api/rooms/' + encodeURIComponent(room) + '/messages').then(r => r.json()).then(messages => {
  document.querySelector('#history').replaceChildren(...messages.map(message => {
    const item = document.createElement('li');
    item.textContent = message.user + ': ' + message.text;
    return item;
  }));
});
"""

def realtime_app(bugs: frozenset = frozenset()) -> web.Application:
    sockets: dict[str, set] = defaultdict(set)
    streams: dict[str, set] = defaultdict(set)
    history: dict[str, list] = defaultdict(list)

    async def publish(room: str, user: str, text: str, origin=None) -> dict:
        message = {"type": "message", "id": secrets.token_hex(6), "room": room, "user": user, "text": text, "ts": now()}
        history[room] = (history[room] + [message])[-50:]
        target = "*" if "leak_rooms" in bugs else room
        rooms = list(sockets) if target == "*" else [room]
        for name in rooms:
            for ws in list(sockets[name]):
                if "no_broadcast" in bugs and ws is not origin:
                    continue
                await ws.send_str(json.dumps(message))
            for queue in list(streams[name]):
                queue.put_nowait(message)
        return message

    async def ui(_):
        return page("Chat", "<h1>Chat</h1><ul id='history'></ul><input id='text'><button>Send</button>", CHAT_SCRIPT)

    async def ws_handler(request):
        room, user = request.query.get("room", "general"), request.query.get("user", "anon")
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        sockets[room].add(ws)
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                data = json.loads(msg.data)
                text = str(data.get("text", ""))
                if data.get("type") == "message" and 1 <= len(text) <= 1000:
                    await publish(room, user, text, origin=ws)
        finally:
            sockets[room].discard(ws)
        return ws

    async def events(request):
        room = request.match_info["room"]
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"})
        await response.prepare(request)
        queue: asyncio.Queue = asyncio.Queue()
        streams[room].add(queue)
        try:
            await response.write(b": connected\n\n")
            while True:
                message = await queue.get()
                await response.write(f"data: {json.dumps(message)}\n\n".encode())
        finally:
            streams[room].discard(queue)

    async def post_message(request):
        body = await json_body(request)
        text = str(body.get("text", ""))
        if not 1 <= len(text) <= 1000:
            return error(400, "invalid message")
        return web.json_response(await publish(request.match_info["room"], str(body.get("user", "anon")), text), status=201)

    async def get_history(request):
        return web.json_response(history[request.match_info["room"]])

    app = web.Application()
    app.router.add_get("/", ui)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/api/rooms/{room}/events", events)
    app.router.add_post("/api/rooms/{room}/messages", post_message)
    app.router.add_get("/api/rooms/{room}/messages", get_history)
    return app


# -- serving ---------------------------------------------------------------------------------

class Server:
    """Runs an aiohttp app on a background thread: `with Server(app) as url: ...`."""

    def __init__(self, app: web.Application) -> None:
        self.app = app
        self.loop = asyncio.new_event_loop()
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.runner = web.AppRunner(app, handle_signals=False, shutdown_timeout=0.1)

    def __enter__(self) -> str:
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self._start(), self.loop).result(10)
        return f"http://127.0.0.1:{self.port}"

    async def _start(self) -> None:
        await self.runner.setup()
        await web.TCPSite(self.runner, "127.0.0.1", self.port).start()

    def __exit__(self, *_) -> None:
        asyncio.run_coroutine_threadsafe(self._stop(), self.loop).result(10)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)
        self.loop.close()

    async def _stop(self) -> None:
        await self.runner.cleanup()
        # Long-lived handlers (SSE streams) must finish before the loop closes.
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
