# ✅ API / Backend Service on Render with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-zpbtt-api-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-zpbtt-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 30s | 5m 57s | 9m 39s |
| Turns | 12 | 13 | |
| Tokens | 484.4K | 814.7K | 1.61M |
| Agent cost | $0.46 | $0.42 | $1.13 |
| Shell commands | 11 | 12 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 11s, 312.8K tokens, $0.24).

## Screenshots

**The API documentation at /docs** (https://adb-zpbtt-api-web.onrender.com/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Python 3.12
- Frameworks: FastAPI
- Data: PostgreSQL (Render Postgres, free)
- Libraries: Uvicorn, psycopg, SQLAlchemy
- Dev tools: HTTPX, pytest
- Packaging: Render Blueprint (render.yaml)
- Hosting: Render web service (free, running the prebuilt image python:3.12-slim)
- Code: 466 lines in 17 files (Python 395, Shell 71, Markdown 41, YAML 26, JSON 10)
- Dependencies: 0 npm, 6 Python
- Deploy config: `render.yaml`

### Stack fit

**81/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Python 3.12 + FastAPI + SQLAlchemy + Render Postgres is a well-reasoned, proportionate fit for a small authenticated JSON API, and STACK.md justifies it soundly. The deployment departed from the planned native-runtime Blueprint for a runtime-install workaround on a stock image, which weakens its fit with the platform.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | FastAPI covers the required validation, the OpenAPI document and the HTML docs out of the box, and managed Postgres through SQLAlchemy Core is a durable store. An in-process limiter suits the single instance. |
| Proportion | 30 | 9/10 | Four pinned dependencies, one web service and one database is minimal. The only extra is the SQLite fallback, kept for local development. |
| Platform fit | 30 | 6/10 | STACK.md and render.yaml plan the idiomatic native Python runtime with a Blueprint-wired DATABASE_URL. Without git access, the build instead ran a stock image that unpacks an env var tarball and runs pip at each boot, which fights Render's build and deploy model and lengthens free-tier cold starts. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**68/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.39) of the process, the code, the hosting plan and the live app.

The FastAPI Notes API on Render is functionally solid. It handles secrets well, scopes every query to the owner, validates input strictly and exposes nothing beyond the documented endpoints over valid HTTPS. Its main weaknesses come from the deployment: code ships in an env var and pip installs at every boot onto an unpinned python:3.12-slim image, the container runs as root, and the free Postgres was probably left open to external connections and expires on 2026-11-25, which undermines the persistence requirement.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS and DATABASE_URL are set as Render service env vars through the API. The scripts read the bench keys and the Render token from the environment and never print them, and no secret appears in source, transcripts or the shipped tarball. A minor gap: the deploy script pulls the DB connection string itself and sends it as a plain env var, when render.yaml's fromDatabase wiring would have avoided handling it. |
| Deployment provenance | 20 | 4/10 | No image or build artifact was produced. The app code travels as a base64 tarball in an env var and is unpacked onto the mutable tag python:3.12-slim at every boot. pip then installs from PyPI on each start, with top-level versions pinned but transitive dependencies unpinned and no hashes, so what runs can change with any restart or wake from sleep. |
| Terms compliance | 15 | 6/10 | Render's free plan allows a personal side project. However, the free Postgres expires on 2026-11-25, 30 days after creation, which breaks the requirement that notes persist. The free web service also sleeps, so friends' scripts face 30-60 s cold starts that are made worse by the pip install on every boot. The agent disclosed both limits. |
| Least privilege | 15 | 5/10 | The app connects over the database's internal URL. But the database was created through the API without an ipAllowList, so Render's default of allowing external connections from any IP with the password probably applies (render.yaml's ipAllowList: [] was never used). The container also runs as root in the stock python image, because the start command never drops privileges. |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. Responses carry no HSTS, X-Content-Type-Options, frame-protection or CSP headers, and the app could have added them in its middleware. |
| Attack surface | 10 | 9/10 | Probes for /.env, /.git/config, source files, /srv and /admin all return a JSON 404, and errors leak no stack traces. Only the documented /docs, /openapi.json and /health are public, plus FastAPI's default /redoc, which is harmless. |
| Application security | 5 | 8/10 | Pydantic strict types with length caps, parameterised SQLAlchemy queries, every query scoped to the owner (404 for other keys) and a per-key sliding-window limiter returning 429 with Retry-After are all solid. Requests with no key or a bad key are never rate-limited, and the limiter's counts live in memory, so they reset whenever the instance restarts or sleeps. |

Findings:

- **medium** · deployment · Code shipped in an env var and dependencies installed at runtime on a mutable base image: app/scripts/render_image_deploy.py:10-14 (BOOT: echo "$APP_TGZ_B64" | base64 -d | tar xz && pip install ... -r requirements.txt) and :54 imagePath docker.io/library/python:3.12-slim; process/resources.json source docker.io/library/python:3.12-slim Fix: Build an immutable image (or a Render native build from a repo the owner controls) with the base image pinned by digest and a fully locked requirements file installed with --require-hashes at build time, not at boot.
- **medium** · deployment · Free Render Postgres expires after 30 days: process/resources.json: postgres expires_at 2026-11-25T20:10:24Z; TASK.md requires a database that survives restarts and redeploys Fix: Upgrade the database to a paid instance type such as basic-256mb before it expires, or move to a store that does not expire.
- **medium** · deployment · Postgres probably reachable from the internet: process/deploy.md: POST /v1/postgres with no ipAllowList field; render.yaml:27 ipAllowList: [] was never applied Fix: Set the database's ipAllowList to empty (internal connections only) through the API or dashboard.
- **low** · deployment · Container runs as root: render_image_deploy.py:10-14 runs mkdir /srv, pip install and uvicorn directly in the stock python:3.12-slim image, which defaults to root Fix: Use a Dockerfile-built image with a non-root USER.
- **low** · platform · Free web service sleeps and cold starts slowly: process/deployment.json notes: sleeps after 15 min idle, first request takes ~30-60 s because pip install runs on every boot Fix: Use a paid instance if callers need low latency. Installing dependencies at build time would at least shorten cold starts.
- **low** · app · No security headers: curl -D - https://adb-zpbtt-api-web.onrender.com/docs: no strict-transport-security, x-content-type-options, x-frame-options or content-security-policy Fix: Add HSTS, nosniff, frame-ancestors/X-Frame-Options and a CSP in the existing HTTP middleware.
- **low** · app · No throttling of requests with a missing or invalid key; limiter state is per-process: app/app/main.py:115-120 returns 401 before limiter.hit; app/app/ratelimit.py keeps hits in memory Fix: Add per-IP throttling for failed authentication, and if the service ever scales out, keep the counts in a shared store such as Render Key Value.
- **info** · app · Docs page loads an unpinned Swagger UI from a CDN: GET /docs references https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js with no SRI Fix: Pin an exact swagger-ui version with SRI, or serve the assets locally.
- **info** · app · API keys stored only as hashes: app/app/main.py:64-66 owner_id stores sha256(key) in the database Fix: None; good practice.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET /health answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET /health returns {status: ok} | yes | passed |  |
| GET /openapi.json is an OpenAPI 3 document covering /v1/notes | yes | passed |  |
| GET /docs serves human-readable documentation | no | passed |  |
| Requests without an API key get 401 | yes | passed |  |
| Requests with an unknown API key get 401 | yes | passed |  |
| POST /v1/notes creates a note | yes | passed |  |
| Invalid notes are rejected with 400 | yes | passed |  |
| GET /v1/notes/{id} returns the note | yes | passed |  |
| GET /v1/notes lists notes and filters by tag | yes | passed |  |
| Notes are listed newest first | no | passed |  |
| PATCH /v1/notes/{id} updates only the given fields | yes | passed |  |
| Notes are private to the API key that created them | yes | passed |  |
| DELETE /v1/notes/{id} removes the note | yes | passed |  |
| Notes are still there a minute later | yes | passed |  |
| Exceeding 60 requests/minute returns 429 | yes | passed |  |
| 429 responses include a Retry-After header | no | passed |  |
| One key hitting its limit doesn't throttle other keys | yes | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.00 | fixed monthly prices; 0.04 GB out of the Hobby workspace's 5 GB; free instances awake 10 h of 750 free hours |
| Busy | $7.13 | fixed monthly prices; 52.6 GB out of the Hobby workspace's 5 GB, 47.6 GB billed (with a payment method on file; without one Render suspends the services instead); free instances awake 730 h of 750 free hours |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| service | adb-zpbtt-api-web | free | $0.00 | free x 1 instance(s) |
| postgres | adb-zpbtt-api-db | free | $0.00 | Postgres free |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-zpbtt-api-web.onrender.com**, and everything in `TASK.md` passed when I tested it through that URL. No human steps were needed.
>
> **What's deployed (both free plan, $0 a month):**
> - `adb-zpbtt-api-db`: a Render Postgres 16 database (`dpg-dbfr7c2jnfac738k2it0-a`).
> - `adb-zpbtt-api-web`: the web service (`srv-dbfr7qd9fdbs739sgang`). It connects to the database over Render's internal network, and its `API_KEYS` is set to exactly the keys in `BENCH_API_KEYS`.
>
> **Workaround:** there was no GitHub access, so Render couldn't build from a repo. The service instead runs the official public `python:3.12-slim` image, and the app code rides along in an environment variable. At startup it unpacks the code, installs the pinned dependencies and starts the server. `scripts/render_image_deploy.py` creates or updates the service this way. It's an unusual setup but it works.
>
> **Tested through the public URL:**
> - `/health`, `/openapi.json` and `/docs` respond without a key.
> - A missing or wrong key gets `401`.
> - Create, read, list, update and delete all work, including bad input (`400`), unknown notes (`404`) and the tag filter.
> - One key can't see or change another key's notes (`404`).
> - After 60 requests in a minute a key gets `429` with a `Retry-After` header, and the other key is unaffected.
> - A note was still there after I restarted the service. I deleted my test notes afterwards.
>
> **Free-tier limits:**
> - **Sleep:** the service goes to sleep after 15 minutes without traffic, and the next request takes about 30–60 seconds. That's slower than a normal Render build would be, because dependencies are reinstalled on every start.
> - **Database expiry:** the free database expires 30 days after creation. Upgrading it to basic-256mb (about $6 a month) keeps the data.
> - **Rate-limit resets:** rate-limit counts are kept in memory, so they reset whenever the service restarts or sleeps.
>
> The deploy script is committed. `deployment.json` isn't. I didn't create any new credentials, so there's no `.env`.

## Shell commands during deploy

- `6s` `cd /home/runner/work/_temp/adb-zpbtt-api; gh auth status 2>&1|head -2; git remote -v; git log --oneline|head; H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" https://api.render.com/v1/owner`
- `22s` `cd /home/runner/work/_temp/adb-zpbtt-api; H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" -H 'Content-Type: application/json' -X POST https://api.render.com/v1/postgres -d '{"name":"adb-zpb`
- `27s` `cd /home/runner/work/_temp/adb-zpbtt-api; H="Authorization: Bearer $RENDER_API_KEY"; for i in $(seq 30); do s=$(curl -s -H "$H" https://api.render.com/v1/postgres/dpg-dbfr7c2jnfac738k2it0-a | python3 `
- `1m 18s` `cd /home/runner/work/_temp/adb-zpbtt-api; cat > scripts/render_image_deploy.py <<'EOF'`
- `1m 24s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-dbfr7qd9fdbs739sgang; for i in $(seq 40); do st=$(curl -s -H "$H" "https://api.render.com/v1/services/$S/deploys?limit=1" | python3 -c 'import sys,json`
- `1m 42s` `H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" "https://api.render.com/v1/logs?ownerId=tea-db6fig0473hc73eb9aeg&resource=srv-dbfr7qd9fdbs739sgang&limit=40&direction=backward" | python3 -c `
- `2m 10s` ❌ `cd /home/runner/work/_temp/adb-zpbtt-api; python3 - <<'EOF'`
- `2m 12s` `cd /home/runner/work/_temp/adb-zpbtt-api; sed -i "14s/.*/CMD = 'sh -c eval\${IFS}\"\$BOOT\"'/" scripts/render_image_deploy.py; sed -n 14p scripts/render_image_deploy.py; .venv/bin/python scripts/rende`
- `2m 18s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-dbfr7qd9fdbs739sgang; sleep 20; for i in $(seq 40); do st=$(curl -s -H "$H" "https://api.render.com/v1/services/$S/deploys?limit=1" | python3 -c 'impor`
- `3m 44s` `cd /home/runner/work/_temp/adb-zpbtt-api; U=https://adb-zpbtt-api-web.onrender.com; scripts/smoke_test.sh $U; IFS=, read -r K1 K2 _ <<<"$BENCH_API_KEYS"`
- `4m 04s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-dbfr7qd9fdbs739sgang; U=https://adb-zpbtt-api-web.onrender.com; IFS=, read -r K1 K2 _ <<<"$BENCH_API_KEYS"`
- `5m 48s` `cd /home/runner/work/_temp/adb-zpbtt-api; U=https://adb-zpbtt-api-web.onrender.com; IFS=, read -r K1 _ <<<"$BENCH_API_KEYS"`
