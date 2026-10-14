"""Names the technologies a cell's app used: its runtime, frameworks, data stores, libraries,
packaging and the cloud services it ran on.

Records keep raw facts (`code.packages`, `code.base_images`, `code.builtins`, ... and the cloud
resources found); this module turns them into names people recognize. Improving the catalog
improves every run's description, older ones included. Records from before those facts were
collected are described from what they have.
"""

from __future__ import annotations

import re
from typing import Any

# package -> (name, role). Roles are listed in ROLES order; a package's role decides its group.
CATALOG: dict[str, tuple[str, str]] = {
    # Web frameworks and servers
    "express": ("Express", "Framework"), "fastify": ("Fastify", "Framework"), "hono": ("Hono", "Framework"),
    "koa": ("Koa", "Framework"), "@hapi/hapi": ("hapi", "Framework"), "next": ("Next.js", "Framework"),
    "nuxt": ("Nuxt", "Framework"), "@sveltejs/kit": ("SvelteKit", "Framework"), "astro": ("Astro", "Framework"),
    "@remix-run/node": ("Remix", "Framework"), "fastapi": ("FastAPI", "Framework"), "flask": ("Flask", "Framework"),
    "django": ("Django", "Framework"), "starlette": ("Starlette", "Framework"), "aiohttp": ("aiohttp", "Framework"),
    "streamlit": ("Streamlit", "Framework"), "dash": ("Dash", "Framework"), "litestar": ("Litestar", "Framework"),
    "uvicorn": ("Uvicorn", "Server"), "gunicorn": ("Gunicorn", "Server"), "hypercorn": ("Hypercorn", "Server"),
    "serve": ("serve", "Server"), "http-server": ("http-server", "Server"),
    # Front end
    "react": ("React", "UI"), "react-dom": ("React", "UI"), "vue": ("Vue", "UI"), "svelte": ("Svelte", "UI"),
    "preact": ("Preact", "UI"), "solid-js": ("Solid", "UI"), "htmx.org": ("htmx", "UI"), "alpinejs": ("Alpine.js", "UI"),
    "tailwindcss": ("Tailwind CSS", "UI"), "vite": ("Vite", "Build"), "esbuild": ("esbuild", "Build"),
    "webpack": ("webpack", "Build"), "typescript": ("TypeScript", "Build"), "tsx": ("tsx", "Build"),
    # Charts
    "chart.js": ("Chart.js", "Charts"), "recharts": ("Recharts", "Charts"), "d3": ("D3", "Charts"),
    "echarts": ("ECharts", "Charts"), "plotly.js": ("Plotly", "Charts"), "plotly.js-dist-min": ("Plotly", "Charts"),
    "plotly": ("Plotly", "Charts"), "apexcharts": ("ApexCharts", "Charts"), "uplot": ("uPlot", "Charts"),
    "@observablehq/plot": ("Observable Plot", "Charts"), "altair": ("Altair", "Charts"),
    # Realtime
    "ws": ("ws", "Realtime"), "socket.io": ("Socket.IO", "Realtime"), "socket.io-client": ("Socket.IO", "Realtime"),
    "websockets": ("websockets", "Realtime"), "pusher": ("Pusher", "Realtime"), "ably": ("Ably", "Realtime"),
    "@vercel/functions": ("Vercel Functions helpers", "Platform"),
    # Data access
    "pg": ("node-postgres", "Database"), "postgres": ("Postgres.js", "Database"),
    "@neondatabase/serverless": ("Neon serverless driver", "Database"), "@vercel/postgres": ("Vercel Postgres SDK", "Database"),
    "better-sqlite3": ("better-sqlite3", "Database"), "sqlite3": ("sqlite3", "Database"), "mysql2": ("mysql2", "Database"),
    "mongodb": ("MongoDB driver", "Database"), "mongoose": ("Mongoose", "Database"), "redis": ("node-redis", "Database"),
    "ioredis": ("ioredis", "Database"), "@upstash/redis": ("Upstash Redis SDK", "Database"),
    "@vercel/kv": ("Vercel KV SDK", "Database"), "@vercel/blob": ("Vercel Blob SDK", "Database"),
    "psycopg": ("psycopg", "Database"), "psycopg2": ("psycopg2", "Database"), "psycopg2-binary": ("psycopg2", "Database"),
    "asyncpg": ("asyncpg", "Database"), "aiosqlite": ("aiosqlite", "Database"), "redis-py": ("redis-py", "Database"),
    "prisma": ("Prisma", "ORM"), "@prisma/client": ("Prisma", "ORM"), "drizzle-orm": ("Drizzle", "ORM"),
    "kysely": ("Kysely", "ORM"), "sequelize": ("Sequelize", "ORM"), "typeorm": ("TypeORM", "ORM"),
    "knex": ("Knex", "ORM"), "sqlalchemy": ("SQLAlchemy", "ORM"), "sqlmodel": ("SQLModel", "ORM"),
    # Auth, security and validation
    "bcrypt": ("bcrypt", "Auth"), "bcryptjs": ("bcrypt.js", "Auth"), "argon2": ("Argon2", "Auth"),
    "@node-rs/argon2": ("Argon2", "Auth"), "jsonwebtoken": ("jsonwebtoken", "Auth"), "jose": ("jose", "Auth"),
    "passlib": ("passlib", "Auth"), "pyjwt": ("PyJWT", "Auth"), "express-session": ("express-session", "Auth"),
    "cookie-parser": ("cookie-parser", "Auth"), "helmet": ("Helmet", "Security"), "cors": ("cors", "Security"),
    "express-rate-limit": ("express-rate-limit", "Security"), "slowapi": ("SlowAPI", "Security"),
    "zod": ("Zod", "Validation"), "joi": ("Joi", "Validation"), "pydantic": ("Pydantic", "Validation"),
    # Data processing
    "pandas": ("pandas", "Data processing"), "numpy": ("NumPy", "Data processing"), "polars": ("Polars", "Data processing"),
    "csv-parse": ("csv-parse", "Data processing"), "papaparse": ("Papa Parse", "Data processing"),
    # Testing
    "jest": ("Jest", "Testing"), "vitest": ("Vitest", "Testing"), "mocha": ("Mocha", "Testing"),
    "supertest": ("SuperTest", "Testing"), "playwright": ("Playwright", "Testing"), "@playwright/test": ("Playwright", "Testing"),
    "pytest": ("pytest", "Testing"), "httpx": ("HTTPX", "Testing"),
}
# Python packages among the catalog's, to tell ecosystems apart in records without `packages`.
PYTHON_PACKAGES = {
    "fastapi", "flask", "django", "starlette", "aiohttp", "streamlit", "dash", "litestar", "uvicorn", "gunicorn",
    "hypercorn", "websockets", "psycopg", "psycopg2", "psycopg2-binary", "asyncpg", "aiosqlite", "redis-py", "sqlalchemy",
    "sqlmodel", "passlib", "pyjwt", "slowapi", "pydantic", "pandas", "numpy", "polars", "plotly", "altair", "pytest", "httpx",
}
ROLES = ("Framework", "Server", "UI", "Charts", "Realtime", "Database", "ORM", "Auth", "Security", "Validation",
         "Data processing", "Platform", "Build", "Testing")
IGNORED = re.compile(r"^@types/")  # type declarations say nothing about the stack
CONFIG_NAMES = {
    "render.yaml": "Render Blueprint (render.yaml)", "vercel.json": "vercel.json", ".do/app.yaml": "App spec (.do/app.yaml)",
    "app.yaml": "App spec (app.yaml)", "Procfile": "Procfile", "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose", "compose.yaml": "Docker Compose", "fly.toml": "fly.toml",
    "netlify.toml": "netlify.toml", "nginx.conf": "nginx config",
}
IMAGE_RUNTIMES = (("node", "Node.js"), ("python", "Python"), ("nginx", "nginx"), ("caddy", "Caddy"), ("httpd", "Apache httpd"),
                  ("oven/bun", "Bun"), ("denoland/deno", "Deno"), ("golang", "Go"))


def describe(record: dict[str, Any]) -> dict[str, list[str]]:
    """The technologies one cell used, by group: Runtime, Frameworks, Data, Libraries, Dev tools,
    Packaging and Hosting. Groups with nothing in them are left out."""
    code = record.get("code") or {}
    resources = record.get("resources") or []
    declared = code.get("packages") or {}
    runtime_packages = [p for p in (declared.get("npm") or []) + (declared.get("python") or []) if not IGNORED.match(p)]
    if not declared:  # records from before packages were recorded only kept the notable ones
        runtime_packages = list(code.get("frameworks") or [])
    dev_packages = [p for p in (declared.get("npm_dev") or []) + (declared.get("python_dev") or []) if not IGNORED.match(p)]
    builtins = set(code.get("builtins") or [])
    images = list(code.get("base_images") or []) + [image for image in _render_images(resources) if image not in (code.get("base_images") or [])]

    groups: dict[str, list[str]] = {}
    groups["Runtime"] = _runtimes(code, images, runtime_packages)
    hosting = _hosting(resources, code)
    frameworks = _named(runtime_packages, {"Framework", "UI"})
    if not frameworks and any(h.startswith("Vercel project") for h in hosting):
        # Vercel serves files from its CDN and runs api/ as functions; a built-in http server in
        # such a project only runs locally.
        frameworks = ["Plain Vercel Functions"] if "api" in (code.get("dirs") or []) else ["Static files"]
    if not frameworks and "node:http" in builtins:
        frameworks = ["Node.js http module (built in)"]
    if not frameworks and "python:http.server" in builtins:
        frameworks = ["Python http.server (built in)"]
    groups["Frameworks"] = frameworks
    groups["Data"] = _data(resources, runtime_packages, builtins)
    groups["Libraries"] = _named(runtime_packages, set(ROLES) - {"Framework", "UI"}, unknown=True)
    groups["Dev tools"] = _named(dev_packages, set(ROLES), unknown=True)
    packaging = [f"Docker ({', '.join(code.get('base_images'))})"] if code.get("base_images") else []
    packaging += [CONFIG_NAMES[c] for c in code.get("deploy_config") or [] if c in CONFIG_NAMES and CONFIG_NAMES[c] not in packaging]
    groups["Packaging"] = packaging
    groups["Hosting"] = hosting
    return {group: names for group, names in groups.items() if names}


def headline(record: dict[str, Any], limit: int = 4) -> list[str]:
    """A few names that sum the stack up: runtime, main framework, then data stores."""
    groups = describe(record)
    names = groups.get("Runtime", [])[:1] + groups.get("Frameworks", [])[:2] + [_short(d) for d in groups.get("Data", [])]
    return list(dict.fromkeys(_short(n) for n in names))[:limit]


def tally(records: list[dict[str, Any]]) -> dict[str, list[tuple[str, int]]]:
    """How many cells used each runtime, framework and data store, most used first."""
    counts: dict[str, dict[str, int]] = {"Runtime": {}, "Frameworks": {}, "Data": {}}
    for record in records:
        groups = describe(record)
        for group in counts:
            for name in dict.fromkeys(_short(n) for n in groups.get(group, [])):
                counts[group][name] = counts[group].get(name, 0) + 1
    return {group: sorted(found.items(), key=lambda kv: (-kv[1], kv[0])) for group, found in counts.items() if found}


# -- groups --------------------------------------------------------------------------------------

def _named(packages: list[str], roles: set[str], unknown: bool = False) -> list[str]:
    by_role: dict[str, list[str]] = {}
    for package in packages:
        name, role = CATALOG.get(package.lower(), (package, "Other"))
        if role in roles or (unknown and role == "Other"):
            by_role.setdefault(role, [])
            if name not in by_role[role]:
                by_role[role].append(name)
    order = [r for r in ROLES if r in by_role] + (["Other"] if "Other" in by_role else [])
    return [name for role in order for name in by_role[role]]


def _runtimes(code: dict[str, Any], images: list[str], packages: list[str]) -> list[str]:
    found = []
    for image in images:
        name = _image_runtime(image)
        if name and name not in found:
            found.append(name)
    hints = code.get("runtime_hints") or {}
    declared = code.get("packages") or {}
    manifests = set(code.get("manifests") or [])
    lines = code.get("lines") or {}
    if declared or manifests:
        node = "package.json" in manifests or "node" in hints or bool(declared.get("npm") or declared.get("npm_dev"))
        python = (any(m.startswith("requirements") or m == "pyproject.toml" for m in manifests) or "python" in hints
                  or bool(declared.get("python") or declared.get("python_dev")))
    else:  # older records: only the notable packages and lines per language
        python = "Python" in lines
        node = ("JavaScript" in lines or "TypeScript" in lines) and any(p not in PYTHON_PACKAGES for p in packages)
    if node and not any(f.startswith("Node.js") for f in found):
        found.append(_versioned("Node.js", hints.get("node")))
    if python and not any(f.startswith("Python") for f in found):
        found.append(_versioned("Python", hints.get("python")))
    if not found and "HTML" in lines:
        found.append("Static files")
    return found


def _image_runtime(image: str) -> str | None:
    """'node:22-alpine' -> 'Node.js 22'; 'python:3.12-slim' -> 'Python 3.12'; 'nginx:1.27' -> 'nginx'."""
    reference = image.split("@")[0]
    for prefix in ("docker.io/library/", "docker.io/", "library/"):
        reference = reference.removeprefix(prefix)
    repository, _, tag = reference.partition(":")
    for name, runtime in IMAGE_RUNTIMES:
        if repository == name or repository.endswith(f"/{name}"):
            version = re.match(r"^(\d+(?:\.\d+)?)", tag)
            if runtime == "Node.js" and version:
                return f"Node.js {version.group(1).split('.')[0]}"
            if runtime == "Python" and version:
                return f"Python {version.group(1)}"
            return runtime
    return None


def _versioned(runtime: str, hint: str | None) -> str:
    """'Node.js' with '>=20' -> 'Node.js 20+'; with '22.11.0' -> 'Node.js 22'."""
    if not hint:
        return runtime
    match = re.search(r"(\d+(?:\.\d+)?)", hint)
    if not match:
        return runtime
    version = match.group(1).split(".")[0] if runtime == "Node.js" else match.group(1)
    return f"{runtime} {version}" + ("+" if re.match(r"^\s*(>=|\^|~|>)", hint) else "")


def _data(resources: list[dict[str, Any]], packages: list[str], builtins: set[str]) -> list[str]:
    found = []
    kinds = {r.get("kind") for r in resources}
    for r in resources:
        kind, plan, details = r.get("kind"), str(r.get("plan") or ""), r.get("details") or {}
        if kind == "postgres":
            found.append(f"PostgreSQL (Render Postgres{', ' + plan if plan else ''})")
        elif kind == "key_value":
            found.append(f"Redis-compatible (Render Key Value{', ' + plan if plan else ''})")
        elif kind == "database":
            engine = {"pg": "PostgreSQL", "mysql": "MySQL", "redis": "Redis", "valkey": "Valkey", "mongodb": "MongoDB"}.get(
                str(details.get("engine")).lower(), str(details.get("engine") or "Database"))
            found.append(f"{engine} (DigitalOcean Managed Database)")
        elif kind == "app" and "dev database" in plan:
            found.append("PostgreSQL (App Platform dev database)")
        elif kind == "blob_store":
            found.append("Vercel Blob")
        elif kind == "integration_store":
            product = str(details.get("product") or "Marketplace store")
            found.append({"neon": "PostgreSQL (Neon)", "upstash-redis": "Redis (Upstash)", "upstash": "Redis (Upstash)",
                          "supabase": "PostgreSQL (Supabase)"}.get(product, f"{product} (Vercel Marketplace)"))
        elif kind == "global_config":
            found.append("Vercel Edge Config")
    sqlite = "node:sqlite" in builtins or "python:sqlite3" in builtins or bool({"better-sqlite3", "sqlite3", "aiosqlite"} & set(packages))
    volume = any(r.get("kind") == "project" and (r.get("details") or {}).get("volume_enabled") for r in resources) or "volume" in kinds
    if sqlite:
        found.append("SQLite (on a persistent volume)" if volume else "SQLite")
    elif volume:
        found.append("Files on a persistent volume")
    return list(dict.fromkeys(found))


def _render_images(resources: list[dict[str, Any]]) -> list[str]:
    return [str((r.get("details") or {}).get("source")) for r in resources
            if r.get("kind") == "service" and (r.get("details") or {}).get("runtime") == "image" and (r.get("details") or {}).get("source")]


def _hosting(resources: list[dict[str, Any]], code: dict[str, Any]) -> list[str]:
    found = []
    for r in resources:
        kind, plan, details = r.get("kind"), str(r.get("plan") or ""), r.get("details") or {}
        if kind == "service":
            what = {"static_site": "Render static site", "background_worker": "Render background worker",
                    "private_service": "Render private service", "cron_job": "Render cron job"}.get(details.get("type"), "Render web service")
            source = str(details.get("source") or "")
            how = (f", running the prebuilt image {_image_name(source)}" if details.get("runtime") == "image" and source
                   else f", built from {source.removeprefix('https://github.com/')}" if source.startswith("https://github.com/")
                   else f", {details.get('runtime')} runtime" if details.get("runtime") else "")
            found.append(f"{what} ({plan or 'plan unknown'}{how})")
        elif kind == "app":
            for part in [p.strip() for p in plan.split(",") if p.strip()]:
                component, _, size = part.partition(": ")
                if size and size != "dev database":
                    found.append(f"App Platform service ({size.split(' x ')[0]}" + (f" × {size.split(' x ')[1]}" if " x " in size and size.split(" x ")[1] != "1" else "") + ")")
            if plan == "static":
                found.append("App Platform static site")
        elif kind == "registry":
            found.append(f"DigitalOcean Container Registry ({plan or 'plan unknown'})")
        elif kind == "droplet":
            found.append(f"Droplet ({plan})")
        elif kind == "project" and "hourly_usd" in details or (kind == "project" and "volume_enabled" in details):
            found.append(f"Cloudish container ({plan or 'default size'})" + (" with a persistent volume" if details.get("volume_enabled") else ""))
        elif kind == "project" and "framework" in details:
            framework = {"nextjs": "Next.js"}.get(str(details.get("framework")), details.get("framework"))
            found.append("Vercel project" + (f" ({framework})" if framework else ""))
            if "api" in (code.get("dirs") or []) or framework:
                found.append("Vercel Functions")
    return list(dict.fromkeys(found))


def _image_name(reference: str) -> str:
    for prefix in ("docker.io/library/", "docker.io/"):
        reference = reference.removeprefix(prefix)
    return reference


def _short(name: str) -> str:
    """'PostgreSQL (Render Postgres, free)' -> 'PostgreSQL'; 'Node.js http module (built in)' -> 'http (built in)'."""
    if name.startswith("Node.js http module"):
        return "Node.js http"
    if name == "Plain Vercel Functions":
        return "Vercel Functions"
    if name.startswith("Python http.server"):
        return "http.server"
    return name.split(" (")[0]
