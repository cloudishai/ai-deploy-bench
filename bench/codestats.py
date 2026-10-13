"""Measures what the agent produced: files, lines by language, dependencies and deploy config."""

from __future__ import annotations

import json
import os
import re
import shutil
import tarfile
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Iterator

from bench.redact import redact_tree

EXCLUDED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".next", ".nuxt", ".output", ".vercel",
    ".svelte-kit", ".turbo", ".cache", ".parcel-cache", "dist", "build", "out", "coverage", "target",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock", "poetry.lock", "uv.lock",
    "Pipfile.lock", "Cargo.lock", "go.sum",
}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".html": "HTML", ".css": "CSS",
    ".scss": "CSS", ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro", ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".sql": "SQL", ".sh": "Shell", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".md": "Markdown",
}
CONFIG_ONLY = {"JSON", "YAML", "TOML", "Markdown"}
DEPLOY_CONFIG = (
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yaml", ".dockerignore", "Procfile",
    "vercel.json", "render.yaml", ".do/app.yaml", ".do/deploy.template.yaml", "app.yaml", "project.yml",
    "nginx.conf", "fly.toml", "netlify.toml",
)
FRAMEWORKS = {
    "next", "react", "vue", "svelte", "@sveltejs/kit", "nuxt", "astro", "vite", "express", "fastify", "hono",
    "koa", "socket.io", "ws", "prisma", "@prisma/client", "drizzle-orm", "pg", "postgres", "better-sqlite3",
    "sqlite3", "mongoose", "chart.js", "recharts", "d3", "plotly.js", "echarts", "tailwindcss",
    "@neondatabase/serverless", "@upstash/redis", "@vercel/postgres", "@vercel/kv", "@vercel/blob", "bcrypt",
    "bcryptjs", "argon2", "jsonwebtoken",
    "fastapi", "flask", "django", "streamlit", "dash", "uvicorn", "gunicorn", "sqlalchemy", "psycopg",
    "psycopg2-binary", "aiohttp", "starlette", "pandas", "plotly", "websockets", "redis",
}
MAX_SNAPSHOT_FILE = 5 * 1024 * 1024


def source_files(root: Path, ignore: set[str]) -> Iterator[Path]:
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative in ignore or name in LOCKFILES or name.startswith(".env") or path.is_symlink():
                continue
            yield path


def dependencies(root: Path) -> dict[str, list[str]]:
    found: dict[str, set[str]] = {"npm": set(), "python": set()}
    for package in root.rglob("package.json"):
        if any(part in EXCLUDED_DIRS for part in package.relative_to(root).parts):
            continue
        try:
            data = json.loads(package.read_text())
        except (ValueError, OSError):
            continue
        for section in ("dependencies", "devDependencies"):
            found["npm"].update((data.get(section) or {}).keys())
    for requirements in root.rglob("requirements*.txt"):
        if any(part in EXCLUDED_DIRS for part in requirements.relative_to(root).parts):
            continue
        for line in requirements.read_text(errors="ignore").splitlines():
            if (name := re.match(r"^\s*([A-Za-z0-9_.\-]+)", line)) and not line.strip().startswith(("#", "-")):
                found["python"].add(name.group(1).lower())
    for pyproject in root.rglob("pyproject.toml"):
        if any(part in EXCLUDED_DIRS for part in pyproject.relative_to(root).parts):
            continue
        try:
            project = tomllib.loads(pyproject.read_text()).get("project") or {}
        except (tomllib.TOMLDecodeError, OSError):
            continue
        for spec in project.get("dependencies") or []:
            if name := re.match(r"^\s*([A-Za-z0-9_.\-]+)", spec):
                found["python"].add(name.group(1).lower())
    return {kind: sorted(names) for kind, names in found.items()}


def stats(root: Path, ignore: set[str]) -> dict[str, Any]:
    lines: dict[str, int] = {}
    files = 0
    for path in source_files(root, ignore):
        files += 1
        language = "Docker" if path.name == "Dockerfile" else LANGUAGES.get(path.suffix.lower())
        if not language:
            continue
        try:
            count = sum(1 for line in path.read_text(errors="ignore").splitlines() if line.strip())
        except OSError:
            continue
        lines[language] = lines.get(language, 0) + count
    deps = dependencies(root)
    all_deps = set(deps["npm"]) | set(deps["python"])
    return {
        "files": files,
        "lines": dict(sorted(lines.items(), key=lambda kv: -kv[1])),
        "code_lines": sum(v for k, v in lines.items() if k not in CONFIG_ONLY),
        "dependencies": {kind: len(names) for kind, names in deps.items()},
        "frameworks": sorted(all_deps & FRAMEWORKS),
        "deploy_config": [name for name in DEPLOY_CONFIG if (root / name).exists()],
        "git_repo": (root / ".git").exists(),
    }


def snapshot(root: Path, destination: Path, ignore: set[str], secrets: list[str]) -> int:
    """Archives the workspace source (no dependencies, build output or .env files), redacted."""
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / root.name
        count = 0
        for path in source_files(root, ignore):
            if path.stat().st_size > MAX_SNAPSHOT_FILE:
                continue
            target = staging / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            count += 1
        staging.mkdir(parents=True, exist_ok=True)
        redact_tree(staging, secrets)
        with tarfile.open(destination, "w:gz") as archive:
            archive.add(staging, arcname=root.name)
    return count
