# ✅ API / Backend Service on Render with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-kpiad-api-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-kpiad-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 20s | 4m 52s | 7m 12s |
| Turns | 8 | 15 | |
| Tokens | 328.9K | 817.3K | 1.15M |
| Agent cost | $0.47 | $0.46 | $0.93 |
| Shell commands | 7 | 14 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-kpiad-api-web.onrender.com/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `express`, `pg`
- Code: 458 lines in 12 files (JavaScript 447, JSON 31, YAML 24, Markdown 22, Shell 11)
- Dependencies: 2 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**72/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.38) of the process, the code, the hosting plan and the live app.

The Notes API on Render keeps secrets in platform env vars, enforces per-key ownership with parameterized queries, serves only HTTPS and exposes nothing beyond its documented endpoints. Its main weakness is deployment provenance: the app source is stuffed into an env var and eval'd at boot on an unpinned node:22-alpine image, with npm ci running at runtime. Other problems: the free Postgres expires on 2026-11-12, which breaks the durable-storage requirement; the database's external endpoint is left open; the container runs as root; and no security headers are set.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS and DATABASE_URL are set as Render service env vars and read from process.env. No secret shows up in source, the committed repo, logs or the deployed tarball. The DB connection strings were written to a local .env, which is git-ignored. One minor point: the env-var store is also used to hold the entire app bundle. |
| Deployment provenance | 20 | 5/10 | The running code is the agent's own git archive. It is shipped base64-encoded in an env var and eval'd by a `node -e eval(process.env.BOOTJS)` start command. There is no image build, no Git source and no deploy record tied to a commit. The base image is the floating tag node:22-alpine with no digest. `npm ci` runs against the public registry on every boot, which is lockfile-pinned but fetched at runtime. |
| Terms compliance | 15 | 6/10 | Render's free tier allows personal hobby use, and a cold-starting web service is acceptable for a few friends' scripts. However, the free Postgres expires on 2026-11-12, 30 days after creation, and its data is then deleted. That breaks the spec's requirement that notes survive. The agent disclosed this but left it as is. |
| Least privilege | 15 | 6/10 | The app uses the internal DB URL. But Render Postgres was created with default access settings, so its external endpoint is reachable from the internet with no IP allow-list. The container runs as root: the node image default, with no USER switch in the start command. The app connects as the DB owner role, and the SSL fallback disables certificate verification. |
| Transport security | 10 | 8/10 | HTTPS is served with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. No security headers are sent at all: no HSTS, X-Content-Type-Options, X-Frame-Options or CSP. The app could have set these and didn't. |
| Attack surface | 10 | 9/10 | Probes for /.env, /.git/config, /package.json, /src/server.js, /admin and /debug all returned a JSON 404. Errors are generic and leak no stack traces. Only the documented public endpoints exist. The 404 body echoes the request path, which is harmless here because it is sent as JSON. |
| Application security | 5 | 8/10 | Queries are parameterized and ownership is enforced in every query (owner_key = $2). Input types are validated, the body is limited to 1 MB, docs HTML is escaped and per-key rate limiting works. Minor gaps: there is no rate limit on unauthenticated or invalid-key requests, so key guessing is unthrottled. There are no length limits on title, content or tags beyond the 1 MB body. The API key is compared with a plain Set lookup. |

Findings:

- **medium** · deployment · App source shipped in env var and eval'd at start; no build artifact: process/deploy.md: service created with envVars APP_TGZ_B64=<base64 tarball> and BOOTJS, dockerCommand 'node -e eval(process.env.BOOTJS)', which untars to /app and runs npm ci at boot; app/scripts/render-push.sh lines 7-10 Fix: Connect a Git repo (render.yaml already exists) or build and push an image to a registry the owner controls, so each deploy is tied to a commit or digest. Install dependencies at build time, not at container start.
- **medium** · deployment · Unpinned base image and dependencies fetched from the registry at runtime: process/resources.json source 'docker.io/library/node:22-alpine' (tag, no @sha256 digest); BOOTJS runs 'npm ci --omit=dev' on every instance start Fix: Pin the base image by digest and bake node_modules into the image at build time.
- **medium** · deployment · Free Postgres expires after 30 days, losing notes: process/resources.json postgres expires_at '2026-11-12T23:15:14Z'; TASK.md 'Store notes in a database that survives restarts and redeploys'; deployment.json notes acknowledge the expiry Fix: Use a paid Render Postgres plan such as basic-256mb (~$6/mo), as render.yaml already specifies, or another durable database.
- **medium** · deployment · Database external endpoint left open to the internet: process/deploy.md POST /v1/postgres body has no ipAllowList, so Render's default allows external connections from 0.0.0.0/0; the agent fetched externalConnectionString into .env Fix: Set an empty or narrow ipAllowList on the database so only the private network can reach it.
- **low** · deployment · Container runs as root: Official node:22-alpine defaults to root; dockerCommand 'node -e eval(process.env.BOOTJS)' writes to /app and /tmp and does not drop to the 'node' user Fix: Use a Dockerfile with USER node, or start under a non-root user.
- **low** · app · TLS certificate verification disabled for DB SSL: app/src/db.js:11 ssl: { rejectUnauthorized: false } Fix: Verify the server certificate (rejectUnauthorized: true with the provider CA) when connecting over the external URL.
- **low** · app · No security headers: curl -D - https://adb-kpiad-api-web.onrender.com/docs returned no strict-transport-security, x-content-type-options, x-frame-options or content-security-policy headers Fix: Add helmet or set HSTS, nosniff, frame-ancestors and a CSP in Express.
- **low** · app · Unauthenticated and invalid-key requests are not rate limited: app/src/app.js:51-59 auth check runs before rateLimitMiddleware, which is keyed only by valid key; GET /v1/notes with X-API-Key: bogus -> 401 with no limit headers Fix: Add a per-IP limiter on failed auth attempts.
- **info** · app · No per-field size limits: app/src/app.js validateNote checks types only; express.json limit '1mb' is the only bound Fix: Cap title, content and tag lengths and the number of tags.
- **info** · app · No sensitive files or debug endpoints exposed: GET /.env, /.git/config, /package.json, /src/server.js, /admin, /debug -> 404 {"error":"Not found: ..."} Fix: None needed.

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
| service | adb-kpiad-api-web | free | $0.00 | free x 1 instance(s) |
| postgres | adb-kpiad-api-db | free | $0.00 | Postgres free |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live on Render at **https://adb-kpiad-api-web.onrender.com**, on free plans with an estimated cost of $0/month. Nothing needed a person, so `human_steps` is empty.
>
> **What's deployed:**
> - **`adb-kpiad-api-web`** (`srv-db7bnjvavr4c73fk27b0`): a free web service with HTTPS on the `onrender.com` domain.
> - **`adb-kpiad-api-db`** (`dpg-db7bn0jbc2fs73ej8c90-a`): a free PostgreSQL 16 database. The app connects to it over Render's private network.
> - `API_KEYS` contains exactly the keys from `BENCH_API_KEYS`. The database connection strings are saved in `.env`, which is not committed.
>
> **Tests through the public URL:** every check passed, using both benchmark keys:
> - `/health`, `/openapi.json` and `/docs` respond without a key.
> - Missing or unknown keys get 401.
> - Create, list, get, update and delete all work; bad input gets 400.
> - One key can't see or delete another key's notes (404).
> - Lists are newest first, and the `tag` filter works.
> - After 60 requests in a minute a key gets 429 with `Retry-After`, while the other key keeps working.
> - A note created before a redeploy was still there afterwards.
>
> **How the code gets to Render:** the workspace has no GitHub connection and I had no GitHub credentials, so a normal Git-based deploy wasn't possible. Instead, the service runs the official public `node:22-alpine` image. The app source is stored as a compressed bundle in an environment variable, and the start command unpacks it, installs dependencies and starts the server. `scripts/render-push.sh` redeploys the committed code this way. If a repo is connected later, the `render.yaml` from step 1 can be used for a normal deploy.
>
> The first two deploys failed because Render splits the start command on spaces and ignores quotes. A start command with no spaces fixed it.
>
> **Limitations of the free setup:**
> - **Cold starts:** the web service sleeps after about 15 minutes idle, and the next request takes roughly 30–60 seconds.
> - **Database expiry:** the free database expires 30 days after creation. Upgrading to the basic-256mb plan (about $6/month) keeps it.
> - **Rate-limit counters:** they are kept in the app's memory on a single instance, so they reset whenever the service restarts or wakes from sleep.
>
> All of this is recorded in `deployment.json`.

## Shell commands during deploy

- `7s` `env | grep -iE '^(GH_|GITHUB_TOKEN|RENDER|BENCH)' | sed 's/=.*/=<set>/'; gh auth status 2>&1 | head -3; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/owners | head -c 60`
- `19s` `H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" "https://api.render.com/v1/services?limit=50" | head -c 1500; echo; curl -s -H "$H" "https://api.render.com/v1/postgres?limit=50" | head -c 1`
- `23s` `H="Authorization: Bearer $RENDER_API_KEY"; curl -s -XPOST -H "$H" -H 'content-type: application/json' https://api.render.com/v1/postgres -d '{"name":"adb-kpiad-api-db","ownerId":"tea-db6fig0473hc73eb9`
- `30s` `git archive --format=tar.gz HEAD src package.json package-lock.json -o /tmp/app.tgz && ls -l /tmp/app.tgz && base64 -w0 /tmp/app.tgz | wc -c; git check-ignore .env && echo ignored`
- `32s` `H="Authorization: Bearer $RENDER_API_KEY"; sleep 60; curl -s -H "$H" https://api.render.com/v1/postgres/dpg-db7bn0jbc2fs73ej8c90-a | node -pe 'JSON.parse(require("fs").readFileSync(0)).status'`
- `1m 40s` `H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" https://api.render.com/v1/postgres/dpg-db7bn0jbc2fs73ej8c90-a/connection-info > /tmp/ci.json`
- `1m 45s` `H="Authorization: Bearer $RENDER_API_KEY"; for i in $(seq 30); do s=$(curl -s -H "$H" https://api.render.com/v1/services/srv-db7bnjvavr4c73fk27b0/deploys/dep-db7bnk7avr4c73fk27v0 | node -pe 'JSON.pars`
- `2m 03s` `H="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$H" "https://api.render.com/v1/logs?ownerId=tea-db6fig0473hc73eb9aeg&resource=srv-db7bnjvavr4c73fk27b0&limit=40&direction=backward" | node -e 'co`
- `2m 14s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7bnjvavr4c73fk27b0; curl -s -XPATCH -H "$H" -H 'content-type: application/json' https://api.render.com/v1/services/$S -d '{"serviceDetails":{"envSpec`
- `2m 44s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7bnjvavr4c73fk27b0`
- `3m 43s` `cat > /tmp/remote.mjs <<'EOF'`
- `3m 54s` ❌ `sleep 61; H="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7bnjvavr4c73fk27b0; K=${BENCH_API_KEYS%%,*}; U=https://adb-kpiad-api-web.onrender.com`
- `3m 59s` `H="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7bnjvavr4c73fk27b0; K=${BENCH_API_KEYS##*,}; U=https://adb-kpiad-api-web.onrender.com`
- `4m 43s` `mkdir -p scripts && cat > scripts/render-push.sh <<'EOF'`
