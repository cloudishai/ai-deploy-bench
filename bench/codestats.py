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


def _manifests(root: Path, pattern: str) -> Iterator[Path]:
    for path in sorted(root.rglob(pattern)):
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            yield path


def packages(root: Path) -> dict[str, list[str]]:
    """Declared dependencies by ecosystem: runtime ones, and development ones (`npm_dev`, `python_dev`)."""
    found: dict[str, set[str]] = {"npm": set(), "npm_dev": set(), "python": set(), "python_dev": set()}
    for package in _manifests(root, "package.json"):
        try:
            data = json.loads(package.read_text())
        except (ValueError, OSError):
            continue
        found["npm"].update((data.get("dependencies") or {}).keys())
        found["npm_dev"].update((data.get("devDependencies") or {}).keys())
    for requirements in _manifests(root, "requirements*.txt"):
        kind = "python_dev" if re.search(r"dev|test", requirements.name) else "python"
        for line in requirements.read_text(errors="ignore").splitlines():
            if (name := re.match(r"^\s*([A-Za-z0-9_.\-]+)", line)) and not line.strip().startswith(("#", "-")):
                found[kind].add(name.group(1).lower())
    for pyproject in _manifests(root, "pyproject.toml"):
        try:
            data = tomllib.loads(pyproject.read_text())
        except (tomllib.TOMLDecodeError, OSError):
            continue
        project = data.get("project") or {}
        groups = [project.get("dependencies") or []], [*(project.get("optional-dependencies") or {}).values(),
                                                        *(data.get("dependency-groups") or {}).values()]
        for kind, lists in zip(("python", "python_dev"), groups):
            for spec in (item for specs in lists for item in specs if isinstance(item, str)):
                if name := re.match(r"^\s*([A-Za-z0-9_.\-]+)", spec):
                    found[kind].add(name.group(1).lower())
    found["npm_dev"] -= found["npm"]
    found["python_dev"] -= found["python"]
    return {kind: sorted(names) for kind, names in found.items()}


def dependencies(root: Path) -> dict[str, list[str]]:
    declared = packages(root)
    return {"npm": sorted(set(declared["npm"]) | set(declared["npm_dev"])),
            "python": sorted(set(declared["python"]) | set(declared["python_dev"]))}


def base_images(root: Path) -> list[str]:
    """The images Dockerfiles build FROM, without references to their own earlier stages."""
    images = []
    for dockerfile in _manifests(root, "Dockerfile*"):
        stages: set[str] = set()
        for line in dockerfile.read_text(errors="ignore").splitlines():
            match = re.match(r"^\s*FROM\s+(?:--\S+\s+)*(\S+)(?:\s+AS\s+(\S+))?", line, flags=re.IGNORECASE)
            if not match:
                continue
            image, stage = match.group(1), match.group(2)
            if image.lower() not in stages and image not in images and image.lower() != "scratch":
                images.append(image)
            if stage:
                stages.add(stage.lower())
    return images


def runtime_hints(root: Path) -> dict[str, str]:
    """Runtime versions the project asks for: package.json engines, .nvmrc, .python-version, ..."""
    hints: dict[str, str] = {}
    for package in _manifests(root, "package.json"):
        try:
            node = (json.loads(package.read_text()).get("engines") or {}).get("node")
        except (ValueError, OSError, AttributeError):
            continue
        if isinstance(node, str):
            hints.setdefault("node", node.strip())
    for name, runtime in ((".nvmrc", "node"), (".node-version", "node"), (".python-version", "python"),
                          ("runtime.txt", "python")):
        if (root / name).is_file():
            value = (root / name).read_text(errors="ignore").strip().splitlines()
            if value:
                hints[runtime] = value[0].removeprefix("python-").strip()
    for pyproject in _manifests(root, "pyproject.toml"):
        try:
            requires = (tomllib.loads(pyproject.read_text()).get("project") or {}).get("requires-python")
        except (tomllib.TOMLDecodeError, OSError):
            continue
        if isinstance(requires, str):
            hints.setdefault("python", requires.strip())
    return hints


# Built-in modules worth naming, since an app that uses them may have no dependencies at all.
BUILTIN_PATTERNS = {
    "node:http": re.compile(r"""(?:require\(\s*|from\s+|import\(\s*)['"](?:node:)?https?['"]"""),
    "node:sqlite": re.compile(r"""['"]node:sqlite['"]"""),
    "python:sqlite3": re.compile(r"^\s*(?:import\s+sqlite3|from\s+sqlite3\s+import)", re.MULTILINE),
    "python:http.server": re.compile(r"^\s*(?:import\s+http\.server|from\s+http\.server\s+import|from\s+http\s+import\s+server)", re.MULTILINE),
}
BUILTIN_SUFFIXES = {"node": (".js", ".mjs", ".cjs", ".ts", ".mts", ".cts"), "python": (".py",)}


def builtins(root: Path, ignore: set[str]) -> list[str]:
    found = set()
    for path in source_files(root, ignore):
        ecosystem = next((e for e, suffixes in BUILTIN_SUFFIXES.items() if path.suffix.lower() in suffixes), None)
        if ecosystem is None or path.stat().st_size > MAX_SNAPSHOT_FILE:
            continue
        text = path.read_text(errors="ignore")
        found.update(name for name, pattern in BUILTIN_PATTERNS.items() if name.startswith(ecosystem) and pattern.search(text))
    return sorted(found)


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
        **facts(root, ignore),
    }


def facts(root: Path, ignore: set[str]) -> dict[str, Any]:
    """What bench.stack names the app's technologies from."""
    return {
        "packages": packages(root),
        "base_images": base_images(root),
        "runtime_hints": runtime_hints(root),
        "builtins": builtins(root, ignore),
        "manifests": sorted({p.name for pattern in ("package.json", "requirements*.txt", "pyproject.toml")
                             for p in _manifests(root, pattern)}),
        "dirs": sorted(p.name for p in root.iterdir() if p.is_dir() and p.name not in EXCLUDED_DIRS)[:30],
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
