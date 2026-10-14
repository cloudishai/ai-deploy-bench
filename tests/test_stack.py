"""Technology facts from a workspace (bench.codestats.facts) and the names bench.stack gives them."""

import json

from bench import codestats, stack


def workspace(tmp_path, files):
    root = tmp_path / "adb-x-app"
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    return root


def test_facts_from_a_node_workspace(tmp_path):
    root = workspace(tmp_path, {
        "package.json": json.dumps({"dependencies": {"express": "^5", "bcryptjs": "^3"},
                                    "devDependencies": {"supertest": "^7", "@types/node": "^22", "express": "^5"},
                                    "engines": {"node": ">=22.13"}}),
        "Dockerfile": "FROM node:24-slim AS build\nRUN npm ci\nFROM build AS test\nFROM --platform=linux/amd64 node:24-slim\n",
        "src/db.js": "import { DatabaseSync } from 'node:sqlite';\n",
        "src/server.js": "const http = require('http');\n",
        "node_modules/x/package.json": json.dumps({"dependencies": {"leftpad": "1"}}),
    })
    facts = codestats.facts(root, set())
    assert facts["packages"] == {"npm": ["bcryptjs", "express"], "npm_dev": ["@types/node", "supertest"],
                                 "python": [], "python_dev": []}
    assert facts["base_images"] == ["node:24-slim"]  # stages built FROM earlier stages aren't images
    assert facts["runtime_hints"] == {"node": ">=22.13"}
    assert facts["builtins"] == ["node:http", "node:sqlite"]
    assert facts["manifests"] == ["package.json"] and facts["dirs"] == ["src"]


def test_facts_from_a_python_workspace(tmp_path):
    root = workspace(tmp_path, {
        "requirements.txt": "fastapi==0.115\nuvicorn[standard]>=0.30\n# a comment\n-r other.txt\n",
        "requirements-dev.txt": "pytest\nhttpx\n",
        "Dockerfile": "FROM python:3.12-slim\n",
        ".python-version": "3.12.7\n",
        "app/store.py": "import sqlite3\n",
    })
    facts = codestats.facts(root, set())
    assert facts["packages"]["python"] == ["fastapi", "uvicorn"]
    assert facts["packages"]["python_dev"] == ["httpx", "pytest"]
    assert facts["runtime_hints"] == {"python": "3.12.7"} and facts["builtins"] == ["python:sqlite3"]


def record(cloud_resources, **code):
    return {"code": {"lines": {"JavaScript": 300, "HTML": 100}, "deploy_config": [], **code}, "resources": cloud_resources}


def test_a_cloudish_container_with_sqlite_on_a_volume():
    described = stack.describe(record(
        [{"kind": "project", "plan": "shared", "details": {"volume_enabled": True, "hourly_usd": 0.01}}],
        packages={"npm": ["express", "bcryptjs"], "npm_dev": ["@types/node", "supertest"]},
        base_images=["node:24-slim"], builtins=["node:sqlite"], manifests=["package.json"],
        deploy_config=["Dockerfile", ".dockerignore"]))
    assert described == {
        "Runtime": ["Node.js 24"], "Frameworks": ["Express"], "Data": ["SQLite (on a persistent volume)"],
        "Libraries": ["bcrypt.js"], "Dev tools": ["SuperTest"], "Packaging": ["Docker (node:24-slim)"],
        "Hosting": ["Cloudish container (shared) with a persistent volume"]}


def test_a_render_service_running_a_prebuilt_image_with_postgres():
    resources = [{"kind": "service", "plan": "free", "details": {"runtime": "image", "type": "web_service",
                                                                  "source": "docker.io/library/node:22-alpine"}},
                 {"kind": "postgres", "plan": "free", "details": {}}]
    described = stack.describe(record(resources, packages={"npm": ["pg"]}, builtins=["node:http"],
                                      manifests=["package.json"], deploy_config=["render.yaml"]))
    assert described["Runtime"] == ["Node.js 22"]  # from the image Render runs, since there's no Dockerfile
    assert described["Frameworks"] == ["Node.js http module (built in)"]
    assert described["Data"] == ["PostgreSQL (Render Postgres, free)"]
    assert described["Hosting"] == ["Render web service (free, running the prebuilt image node:22-alpine)"]
    assert described["Packaging"] == ["Render Blueprint (render.yaml)"]


def test_a_digitalocean_app_with_a_dev_database():
    resources = [{"kind": "app", "plan": "web: apps-s-1vcpu-0.5gb x 2, db: dev database", "details": {}},
                 {"kind": "registry", "plan": "starter", "details": {}}]
    described = stack.describe(record(resources, packages={"npm": ["express", "pg"]}, base_images=["node:22-alpine"],
                                      manifests=["package.json"]))
    assert described["Data"] == ["PostgreSQL (App Platform dev database)"]
    assert described["Hosting"] == ["App Platform service (apps-s-1vcpu-0.5gb × 2)", "DigitalOcean Container Registry (starter)"]
    assert stack.headline(record(resources, packages={"npm": ["express", "pg"]}, base_images=["node:22-alpine"],
                                 manifests=["package.json"])) == ["Node.js 22", "Express", "PostgreSQL"]


def test_vercel_functions_without_a_framework_ignore_the_local_dev_server():
    resources = [{"kind": "project", "plan": None, "details": {"framework": None, "team_id": "t"}},
                 {"kind": "blob_store", "plan": None, "details": {}}]
    described = stack.describe(record(resources, packages={"npm": ["@vercel/blob"]}, builtins=["node:http"],
                                      runtime_hints={"node": ">=20"}, manifests=["package.json"], dirs=["api", "public"],
                                      deploy_config=["vercel.json"]))
    assert described["Runtime"] == ["Node.js 20+"]
    assert described["Frameworks"] == ["Plain Vercel Functions"]
    assert described["Data"] == ["Vercel Blob"] and described["Hosting"] == ["Vercel project", "Vercel Functions"]
    assert stack.headline(record(resources, dirs=["api"], manifests=["package.json"])) == ["Node.js", "Vercel Functions", "Vercel Blob"]


def test_records_from_before_the_facts_are_described_from_what_they_have():
    old = {"code": {"lines": {"JavaScript": 200, "HTML": 90}, "frameworks": ["express", "pg"], "deploy_config": ["Dockerfile"]},
           "resources": [{"kind": "postgres", "plan": "free"}]}
    described = stack.describe(old)
    assert described["Frameworks"] == ["Express"] and described["Data"] == ["PostgreSQL (Render Postgres, free)"]
    assert stack.describe({"code": {"lines": {"HTML": 40, "CSS": 10}}, "resources": []}) == {"Runtime": ["Static files"]}


def test_tally_counts_each_name_once_per_cell():
    cells = [record([], packages={"npm": ["express", "react", "react-dom"]}, base_images=["node:22-alpine"]),
             record([], packages={"npm": ["express"]}, base_images=["node:22-slim"]),
             record([], packages={"python": ["fastapi"]}, base_images=["python:3.12-slim"])]
    assert stack.tally(cells) == {"Runtime": [("Node.js 22", 2), ("Python 3.12", 1)],
                                  "Frameworks": [("Express", 2), ("FastAPI", 1), ("React", 1)]}
