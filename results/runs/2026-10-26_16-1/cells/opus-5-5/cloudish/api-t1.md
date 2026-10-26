# ⚠️ API / Backend Service on Cloudish with Opus 5.5 (trial 1)

**partial** (failed at verify): 19/20 checks passed (95%).

- URL: https://adb-uxt97-api.cloudish.app (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-uxt97-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 3m 04s | 4m 22s | 7m 26s |
| Turns | 18 | 15 | |
| Tokens | 738.0K | 1.03M | 1.77M |
| Agent cost | $0.59 | $0.53 | $1.12 |
| Shell commands | 14 | 14 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed.

## Screenshots

**The API documentation at /docs** (https://adb-uxt97-api.cloudish.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Python 3.12
- Frameworks: FastAPI
- Data: SQLite (on a persistent volume)
- Libraries: Uvicorn
- Dev tools: HTTPX, pytest
- Packaging: Docker (python:3.12-slim)
- Hosting: Cloudish container (shared) with a persistent volume
- Code: 323 lines in 13 files (Python 315, Markdown 47, JSON 18, Docker 8)
- Dependencies: 0 npm, 4 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Python 3.12, FastAPI, Uvicorn and SQLite on a Cloudish volume fit the job well: they deliver durable storage, auto-generated OpenAPI and docs, and correct single-instance rate limiting with minimal moving parts. The build matches the reasoning recorded in STACK.md.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | FastAPI generates the required OpenAPI document and docs and handles validation. SQLite in WAL mode on a persistent volume is a real, durable database for a few friends' scripts. An in-memory per-key limiter is correct with exactly one instance. |
| Proportion | 30 | 9/10 | Two pinned runtime dependencies and the standard-library sqlite3 make up one process with no extra services. This is about as simple as the requirements allow, and nothing is a stand-in that only looks like it works. |
| Platform fit | 30 | 9/10 | Cloudish runs long-lived containers built from a Dockerfile, with volumes for persistence and no managed database, so a single container plus a volume is the natural fit. STACK.md reasons through this correctly, and the build followed it. |

## Human steps

None: the agent needed no human setup at all.

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.45) of the process, the code, the hosting plan and the live app.

The Notes API is a FastAPI + SQLite app in a single Cloudish container with a persistent volume, and its secrets were handled well: the Cloudish key stayed in a local .env left out of the build context, and API_KEYS went into Cloudish's encrypted secrets without ever being printed. The live service has HTTPS only, HSTS, owner-scoped access, parameterized SQL and no exposed files. The main weaknesses: the app runs on a 0.1 free credit that lasts about 9 hours of uptime, the container runs as root, build inputs aren't fully pinned, and there are minor gaps in security headers and input size limits.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish key was written straight to a chmod-600 .env file without being printed, and that file was left out of the build context. API_KEYS was piped from BENCH_API_KEYS into Cloudish's encrypted secrets API and never echoed. No secrets appear in the source, the image or the transcripts. |
| Deployment provenance | 20 | 7/10 | The app was built server-side on Cloudish from a tarball of the agent's own workspace, and the redeploy was checked against the running container logs. However, the base image is a floating tag (python:3.12-slim, not pinned to a digest), and only the top-level Python dependencies are pinned. Transitive dependencies such as starlette and pydantic have no lock file. |
| Terms compliance | 15 | 6/10 | Personal use fits a prepaid-credit container host, and as far as I know Cloudish's terms don't rule it out, though I'm not certain of them. But the app runs on the 0.1 free starting credit, which buys about 9 hours awake (balance is now about $0.097). Once it reaches zero the app stops with 402s until a person tops it up. The agent disclosed this, but marked it non-blocking. After 24 h idle the app sleeps and the first call gets a 503. |
| Least privilege | 15 | 7/10 | There is one container with the SQLite database on a private volume, the smallest size, and no extra public resources. Public 'open' access is needed for a public API. The Dockerfile has no USER directive, so the app runs as root. |
| Transport security | 10 | 8/10 | HTTP returns a 308 redirect to HTTPS, which is served with a valid certificate and HSTS from the platform. The app doesn't set X-Content-Type-Options, frame protection or a CSP, though it easily could. |
| Attack surface | 10 | 9/10 | No source files, .env, .git or database file are reachable. Errors are JSON without stack traces, and TRACE is rejected. /redoc is exposed beyond the required /docs, and the docs pages load Swagger UI from a floating jsDelivr major version, but both are low impact. |
| Application security | 5 | 8/10 | All SQL is parameterized, Pydantic enforces strict types, notes are scoped to the owning key and return 404 to other keys, and the per-key rate limit works. There are no length limits on title, content or tags. Key comparison isn't constant-time, and rate-limit counts reset whenever the container restarts. |

Findings:

- **medium** · deployment · App runs on a 0.1 free credit that lasts about 9 hours awake: process/deployment.json human_steps: '0.1 free credits, enough for about 9 hours... When the balance reaches zero Cloudish stops the app and requests get 402'; process/context.json balance_usd 0.096523; marked "blocking": false Fix: Make topping up the credits (about $7.84/month) a blocking step before handing the app over, or choose funded hosting.
- **medium** · deployment · Container runs as root: app/Dockerfile has no USER directive (FROM python:3.12-slim ... CMD uvicorn) Fix: Create an unprivileged user, give it ownership of /data, and add USER to the Dockerfile.
- **low** · platform · Sleeping app answers the first API call with a 503 HTML page: deploy.md: first request returned the 'Starting up' 503 HTML page; deployment.json notes sleepAfterMinutes=1440 Fix: Use alwaysOn once funded, or document that clients should retry on 503.
- **low** · deployment · Base image tag not pinned to a digest: app/Dockerfile:1 FROM python:3.12-slim Fix: Pin the base image to python:3.12-slim@sha256:<digest>.
- **low** · deployment · Transitive Python dependencies unpinned, no hashes: app/requirements.txt pins only fastapi==0.115.12 and uvicorn==0.34.2, so starlette, pydantic and anyio resolve at build time Fix: Generate a full lock file (pip-compile --generate-hashes or uv lock) and install with --require-hashes.
- **low** · app · No size limits on note fields: app/app/main.py:148-161: title, content and tags have no max_length or max item count Fix: Add max_length to title and content and cap the number and length of tags, and set a request body size limit.
- **low** · app · Missing security headers: curl -sI https://adb-uxt97-api.cloudish.app/health returns only content-type, content-length and strict-transport-security (no X-Content-Type-Options, X-Frame-Options or CSP) Fix: Add middleware that sets X-Content-Type-Options: nosniff, X-Frame-Options: DENY and a restrictive CSP (relaxed for /docs).
- **info** · app · API key comparison not constant-time; rate-limit state in memory: app/app/main.py:198 'if key not in _api_keys()'; main.py:181 _hits kept in memory, so counts reset on restart or wake Fix: Compare keys with hmac.compare_digest. In-memory counts are acceptable with a single instance.
- **info** · app · Docs pages load third-party scripts from a floating CDN version; /redoc also exposed: GET /docs references https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js; GET /redoc returns 200 Fix: Pin the Swagger UI version (or self-host it), and turn off /redoc if it isn't needed (redoc_url=None).

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
| Notes are private to the API key that created them | yes | failed | GET /v1/notes/497872adf2214d0e9620f1370cfceb4b returned 429, expected 404 or 403: {"error":"rate limit exceeded (60 requests per minute)"} |
| DELETE /v1/notes/{id} removes the note | yes | passed |  |
| Notes are still there a minute later | yes | passed |  |
| Exceeding 60 requests/minute returns 429 | yes | passed |  |
| 429 responses include a Retry-After header | no | passed |  |
| One key hitting its limit doesn't throttle other keys | yes | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.11 | containers awake 10 h at their size's hourly rate; no bandwidth charges |
| Busy | $7.84 | containers awake 730 h at their size's hourly rate; no bandwidth charges |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-uxt97-api-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-uxt97-api.cloudish.app**. Every requirement in `TASK.md` passed when tested through that URL with the two `BENCH_API_KEYS` keys. The main open issue is credit: the free balance only covers about 9 hours of the app being awake.
>
> **What's deployed:**
> - **Cloudish key `adb-uxt97-api`:** created without signup through Cloudish's API and saved in `.env`. It came with 0.1 free credits (credits are dollars).
> - **App `adb-uxt97-api-web`:** built on Cloudish from the Dockerfile. It runs on the smallest size (`shared`, 0.1 CPU, 0.2 GB) and costs $0.0107 per hour while awake, about $7.84 a month if it never sleeps.
> - **Storage:** the SQLite database is on a 1 GB volume at `/data`, which isn't billed. A note I created before a redeploy was still there afterwards.
> - **`API_KEYS`:** set to exactly the `BENCH_API_KEYS` value, stored as an encrypted secret. It isn't in the image or in plain config, and no secret was printed.
> - **HTTPS:** plain HTTP redirects to HTTPS.
>
> **What was tested on the public URL:**
> - `/health`, `/openapi.json` and `/docs` work without a key.
> - A missing or unknown key gets `401`.
> - Create, list, get, update and delete all work. List is newest first and the `tag` filter works.
> - Bad input, including malformed JSON, gets `400`.
> - Another key's notes return `404` for get, update, delete and list.
> - The 61st request in a minute gets `429` with `Retry-After`, and the other key keeps working.
>
> **Things to know:**
> - **Credit runs out:** when the balance hits zero, Cloudish stops the app and requests get `402`; the stored notes are kept. Adding credit is the one human step in `deployment.json`, and it isn't blocking. Someone has to open a claim link and top up. I didn't create the link because it expires 30 minutes after it's made; the call that creates one is in `deployment.json`.
> - **Wake-up delay:** to save credit, the app sleeps after 24 hours without requests (the longest Cloudish allows). The first request to a sleeping app gets a `503` "starting up" page for a few seconds, then requests work normally.
> - **Rate-limit counts reset:** they are kept in memory, so a restart or wake-up clears them. This is accurate only because the app runs as a single container, which Cloudish requires when a volume is attached.

## Shell commands during deploy

- `4s` `for u in llms.txt docs api/v1 skill.md; do echo "== $u"; curl -sL -m 20 https://cloudish.ai/$u | head -c 3000; echo; done; echo "BENCH set: ${BENCH_API_KEYS:+yes}"`
- `8s` `curl -sL -m 20 https://cloudish.ai/skill.md | tail -c +3000`
- `16s` `R=$(curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"alias":"adb-uxt97-api","agent":"claude-code","model":"claude-opus-5-5"}') && echo "$R" | python3 -c '`
- `22s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude='.venv' --exclude='data' --exclude='__pycache__' --exclude='.pytest_cache' -czf /tmp/context.tar.gz . && tar -tzf /tmp/`
- `28s` `set -a && . ./.env && set +a && python3 -c 'import json,os;print(json.dumps({"API_KEYS":os.environ["BENCH_API_KEYS"]}))' | curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-uxt97-api/adb-uxt97-ap`
- `1m 15s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/projects/adb-uxt97-api/adb-uxt97-api-web -H "Authorization: Bearer $CLOUDISH_API_KEY" > /tmp/proj.json; python3 -c '`
- `1m 28s` `set -a && . ./.env && set +a && python3 -c '`
- `1m 32s` `set -a && . ./.env && set +a && curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-uxt97-api/adb-uxt97-api-web/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/`
- `1m 54s` `for i in $(seq 20); do c=$(curl -s -o /tmp/h -w "%{http_code}" -m 30 https://adb-uxt97-api.cloudish.app/health); echo "$i $c"; [ "$c" = 200 ] && break; sleep 5; done; cat /tmp/h | head -c 200`
- `2m 11s` `cat > /tmp/scripts/e2e.py <<'EOF'`
- `2m 28s` `set -a && . ./.env && set +a && K=$(python3 -c 'import os;print(os.environ["BENCH_API_KEYS"].split(",")[0].strip())')`
- `3m 33s` `python3 /tmp/scripts/e2e.py https://adb-uxt97-api.cloudish.app --ratelimit | grep -vE "^PASS (each|isolation)"; K=$(python3 -c 'import os;print(os.environ["BENCH_API_KEYS"].split(",")[0].strip())'); c`
- `4m 10s` `cat > deployment.json <<'EOF'`
- `4m 12s` `printf '.env\n.env*\ndeployment.json\n' >> .dockerignore`
