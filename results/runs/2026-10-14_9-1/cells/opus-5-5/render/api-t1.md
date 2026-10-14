# ✅ API / Backend Service on Render with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-drsgc-api-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-drsgc-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 37s | 11m 14s | 13m 50s |
| Turns | 11 | 14 | |
| Tokens | 458.9K | 837.1K | 1.30M |
| Agent cost | $0.53 | $0.66 | $1.18 |
| Shell commands | 10 | 13 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-drsgc-api-web.onrender.com/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `express`, `pg`
- Code: 494 lines in 11 files (JavaScript 494, Markdown 35, JSON 30, YAML 22)
- Dependencies: 2 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**69/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.45) of the process, the code, the hosting plan and the live app.

The Notes API is well built: queries are parameterized, ownership is enforced per key, it's served over HTTPS with an HTTP redirect, nothing beyond the app is exposed, and secrets were passed through Render env vars without leaking. The main weakness is provenance: production runs a locally built bundle smuggled in as a base64 'secret file' on an unpinned node:22-alpine image, with no source repo or lockfile. In addition, the free Postgres database will expire with all its data on 2026-11-13, the database likely accepts external connections, and the container runs as root.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | DATABASE_URL and API_KEYS were passed to Render as service environment variables through the API, built from shell variables so they never appeared in commands or output, and the payload file was deleted afterwards. The only blemish is a local .env holding the external DB URL. It was written with umask 077 and is git-ignored. |
| Deployment provenance | 20 | 4/10 | Production runs an esbuild bundle built on the agent's machine and uploaded as a base64 'secret file'. That makes it opaque and impossible to trace to any source revision. It runs on the floating node:22-alpine tag, and dependencies were installed with caret ranges and no committed lockfile, using an unpinned `npx -y esbuild@0.25`. |
| Terms compliance | 15 | 5/10 | Render's free tier suits a personal hobby project, and sleeping after idle is tolerable for friends' scripts. But the free Postgres database expires on 2026-11-13 (30 days after creation), and its data goes with it. That breaks the requirement that notes survive over time. The agent disclosed this but didn't fix it. |
| Least privilege | 15 | 6/10 | The app connects to Postgres over Render's internal URL, but the database was created without an IP allow list. A full external connection string exists, so the database is probably reachable from the internet with a password. The container also runs as root in the stock node image, because the docker command never drops privileges. |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. Neither the app nor the platform sends HSTS, X-Content-Type-Options, frame protection or CSP, and the app could have added them. |
| Attack surface | 10 | 10/10 | Probes of /.env, /.git/config, /package.json, /src/app.js, /admin and /debug all returned generic JSON 404s. Bad JSON returns a clean error with no stack trace. Only the documented endpoints are exposed. |
| Application security | 5 | 8/10 | All SQL is parameterized, input types are validated, ownership is enforced in every query (other keys get 404), and the docs HTML is escaped. The rate limit applies only after successful authentication, though, and note sizes and counts are only bounded by the 1 MB body limit. |

Findings:

- **high** · deployment · Code shipped as an opaque locally built bundle inside a secret file: process/deploy.md: `npx -y esbuild@0.25 src/server.js --bundle ... | gzip -9c | base64 -w0 > /tmp/bundle/app.b64`, then `secretFiles:[{name:"app.b64",content:...}]` with dockerCommand `/bin/sh /etc/secrets/start.sh`. process/resources.json shows runtime "image", source docker.io/library/node:22-alpine, and no repo. Fix: Deploy from a Git repository the owner controls (Render native Node runtime or a Dockerfile build), or from a versioned image in a registry the owner controls, so the running code traces to a reviewed commit. Don't use secret files to deliver application code.
- **medium** · deployment · Unpinned base image and build tooling, no lockfile: Service image is the floating tag `docker.io/library/node:22-alpine` (deploy.md). The local pull resolved sha256:0a7108bf..., but no digest was pinned. Dependencies were installed with `npm i express pg` (build.md), and package.json uses `^5.3.0` / `^8.23.1` with no package-lock.json in app/. esbuild ran as `npx -y esbuild@0.25`. Fix: Pin the image by digest (node:22-alpine@sha256:...), commit package-lock.json and install with `npm ci`, and add esbuild as a pinned devDependency.
- **medium** · deployment · Free Postgres database expires after 30 days, losing all notes: process/resources.json: postgres adb-drsgc-api-db plan "free", expires_at "2026-11-13T02:31:39Z". TASK.md requires a database that survives restarts and redeploys. deployment.json notes acknowledge the expiry. Fix: Use a paid Render Postgres plan (e.g. basic-256mb), or a persistent store that doesn't expire, so notes survive past 30 days.
- **medium** · deployment · Database created without an IP allow list (external access likely open): deploy.md: POST /v1/postgres body sets no ipAllowList, and connection-info returned an `externalConnectionString`. As far as I know, Render then accepts external connections from any IP (not verifiable without credentials). The app only needs the internal URL. Fix: Set an empty ipAllowList (or restrict it to trusted IPs) to block external connections, since the service uses the internal connection string.
- **low** · platform · Free web service sleeps after idle: process/deployment.json notes: "the web service sleeps after ~15 min idle, so the first request takes extra time"; plan "free" in resources.json. Fix: That's acceptable for a personal project. Move to a paid instance if the friends' clients can't tolerate cold-start delays.
- **low** · deployment · Container runs as root: Service runs the stock node:22-alpine image (default user root) with dockerCommand `/bin/sh /etc/secrets/start.sh`, which execs `node /tmp/app.js` with no USER or privilege drop (deploy.md). Fix: Build an image with `USER node`, or use Render's native Node runtime, which runs as a non-root user.
- **low** · app · No security headers: `curl -sI https://adb-drsgc-api-web.onrender.com/health` returned only date, content-type, etag, rndr-id, server, vary, cf-* headers: no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options or Content-Security-Policy. src/app.js sets none. Fix: Add helmet (or set the headers manually) for HSTS, nosniff, frame-ancestors and a restrictive CSP on /docs.
- **low** · app · Unauthenticated and invalid-key requests are not rate limited: src/app.js: the auth middleware returns 401 before `v1.use(limiter.middleware)`, and the limiter is keyed on req.apiKeyId, which is set only for valid keys. Invalid-key requests are never counted. Fix: Add a per-IP limit for failed authentication attempts, ahead of the per-key limiter.
- **low** · app · No limits on note size or count: src/app.js validateNote checks types only. express.json allows 1 MB bodies, and there is no cap on the number of tags or notes per key, so one key can fill the 1 GB free database. Fix: Cap title/content/tag lengths, tag count, and notes per key.
- **info** · deployment · Local .env holds the external database URL: deploy.md: `umask 077; printf 'DATABASE_URL=%s\nDATABASE_EXTERNAL_URL=%s\nAPI_KEYS=%s\n' ... > .env`. It is git-ignored (app/.gitignore) and was not deployed. Fix: Avoid writing production credentials to local files, or delete them after deployment.

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
| service | adb-drsgc-api-web | free | $0.00 | free x 1 instance(s) |
| postgres | adb-drsgc-api-db | free | $0.00 | Postgres free |

Teardown: 2 deleted

## Agent's deploy summary

> I deployed the Notes API to Render at **https://adb-drsgc-api-web.onrender.com**, and every requirement in `TASK.md` works through that URL. It costs $0/month and no human steps were needed.
>
> **Resources (both on the free plan):**
> - **Web service** `adb-drsgc-api-web` (`srv-db7ejht9fdbs73duqhf0`) in Oregon, with a `/health` health check.
> - **PostgreSQL 16 database** `adb-drsgc-api-db` (`dpg-db7ej2u7bikc73ajlu10-a`). The service connects to it over Render's internal address.
> - `API_KEYS` is set to exactly the keys in `BENCH_API_KEYS`, which I checked against the service's settings.
>
> **How the code got onto Render:** The Render account had no Git provider connected and there were no GitHub credentials, so Render couldn't build from a repo. Instead, the service runs the official public `node:22-alpine` image. The app is bundled into one JavaScript file and uploaded as a Render secret file, and a small `start.sh` secret file unpacks and runs it on start. My first deploy failed because Render passed the quotes in the start command through literally; moving the start logic into `start.sh` fixed it. To ship code changes, rebuild the bundle, re-upload it and redeploy; the steps are in the README.
>
> **Tested through the public URL:**
> - `/health`, `/openapi.json` and `/docs` (HTML) respond.
> - 401 for a missing or unknown key.
> - Create, list (newest first), `tag` filter, get, update and delete all work, with 400s for bad input.
> - Other keys get 404 on notes they don't own.
> - 429 with `Retry-After` after 60 requests a minute, and one key hitting the limit doesn't affect another.
> - A note survived a full redeploy.
>
> One check in my smoke script failed, but the mistake was in the script: it expected 6 path entries in the OpenAPI document, and there are correctly 5.
>
> **Limitations:**
> - **Database expiry:** Render deletes free Postgres databases 30 days after creation unless they're upgraded (for example to `basic-256mb`, about $6/month). After that, the notes would be lost.
> - **Cold starts:** the free web service sleeps after about 15 minutes idle, so the first request after that is slow.
> - **Rate limit counts:** they're kept in memory on the single instance, so they reset whenever the service restarts.
>
> The database connection strings and API keys are saved only in `.env`, which is git-ignored. `deployment.json` has the resource details and these notes.

## Shell commands during deploy

- `5s` `env | cut -d= -f1 | grep -vE '^(PATH|HOME|PWD|SHLVL|_)$' | sort | tr '\n' ' '; echo; gh auth status 2>&1 | head -5`
- `16s` `A="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$A" https://api.render.com/v1/owners | head -c 800; echo; curl -s -H "$A" "https://api.render.com/v1/services?limit=20" | head -c 1500; echo; cur`
- `27s` `mkdir -p /tmp/bundle && npx -y esbuild@0.25 src/server.js --bundle --platform=node --target=node22 --minify --external:pg-native --outfile=/tmp/bundle/app.js 2>&1 | tail -3 && gzip -9c /tmp/bundle/app`
- `37s` `cd /tmp && docker run -d --name tpg -e POSTGRES_PASSWORD=pg -p 5433:5432 postgres:16 >/dev/null && sleep 4 && docker run -d --name tapp --network host -v /tmp/bundle:/etc/secrets:ro -e DATABASE_URL=po`
- `56s` `A="Authorization: Bearer $RENDER_API_KEY"; curl -s -X POST -H "$A" -H content-type:application/json https://api.render.com/v1/postgres -d '{"name":"adb-drsgc-api-db","ownerId":"tea-db6fig0473hc73eb9ae`
- `1m 00s` `A="Authorization: Bearer $RENDER_API_KEY"; for i in $(seq 1 40); do s=$(curl -s -H "$A" https://api.render.com/v1/postgres/dpg-db7ej2u7bikc73ajlu10-a | node -pe 'JSON.parse(require("fs").readFileSync(`
- `1m 54s` `A="Authorization: Bearer $RENDER_API_KEY"`
- `2m 01s` `A="Authorization: Bearer $RENDER_API_KEY"; for i in $(seq 1 40); do s=$(curl -s -H "$A" https://api.render.com/v1/services/srv-db7ejht9fdbs73duqhf0/deploys/dep-db7eji59fdbs73duqijg | node -pe 'JSON.pa`
- `9m 16s` `A="Authorization: Bearer $RENDER_API_KEY"; curl -s -H "$A" "https://api.render.com/v1/logs?ownerId=tea-db6fig0473hc73eb9aeg&resource=srv-db7ejht9fdbs73duqhf0&limit=40&direction=backward" | node -e 'co`
- `9m 32s` `A="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7ejht9fdbs73duqhf0`
- `10m 12s` `cat > /tmp/smoke.mjs <<'EOF'`
- `10m 26s` `A="Authorization: Bearer $RENDER_API_KEY"; S=srv-db7ejht9fdbs73duqhf0; U=https://adb-drsgc-api-web.onrender.com; K=$(echo $BENCH_API_KEYS | cut -d, -f1)`
- `11m 04s` `cat > deployment.json <<'EOF'`
