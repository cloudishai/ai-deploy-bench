# ✅ API / Backend Service on Cloudish with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-24cth-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 30s | 5m 10s | 7m 40s |
| Turns | 12 | 13 | |
| Tokens | 447.9K | 786.4K | 1.23M |
| Agent cost | $0.45 | $0.41 | $0.86 |
| Shell commands | 10 | 12 | |

App answered 0s after the agent finished deploying.

**Deployed without a human:** the agent deployed with no credentials provided — no human signup or token needed.

## Screenshots

**The API documentation at /docs** (https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Python 3.12
- Frameworks: FastAPI
- Data: SQLite (on a persistent volume)
- Libraries: Uvicorn
- Dev tools: HTTPX, pytest
- Packaging: Docker (python:3.12-slim)
- Hosting: Cloudish container (shared) with a persistent volume
- Code: 324 lines in 14 files (Python 314, Markdown 43, JSON 13, Docker 10)
- Dependencies: 0 npm, 4 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**87/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Python, FastAPI and SQLite on a Cloudish persistent volume is a lean, well-reasoned fit for a small authenticated notes API, and the build follows STACK.md exactly.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | FastAPI's built-in OpenAPI and docs cover the /openapi.json and /docs requirements. SQLite in WAL mode on a persistent volume is a real durable database that the agent confirmed survives a redeploy, and an in-process limiter is accurate for the single replica a volume forces. |
| Proportion | 30 | 9/10 | There are two direct dependencies plus the standard-library sqlite3 and no extra services, which is about as small as the requirements allow without resorting to a fake store. |
| Platform fit | 30 | 8/10 | This matches Cloudish's model of a container built from a Dockerfile with a volume, encrypted secrets and scale-to-zero, and STACK.md explains why: Cloudish has no managed database. The cost is cold starts and a single-replica ceiling, which is acceptable at this scale. |

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-24cth-api' (mint a fresh link with GET https://cloudish.ai/api/v1/credits/claim using CLOUDI; n out-of-credit key returns `402` with the alias of the key that ran out: ```json { "error": "This API key is out of cre

## Security and compliance review

**76/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.40) of the process, the code, the hosting plan and the live app.

The Notes API on Cloudish handles secrets well: API_KEYS is an encrypted project secret and nothing leaked into the transcripts, the source or the build context. It is HTTPS-only with a valid certificate and exposes nothing beyond the app. The main weaknesses: the container runs as root, the base image and transitive dependencies are unpinned, and the service runs on a nearly spent $0.10 credit grant with cold-start 503s, so it will stop serving unless the owner adds credits.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS was piped from the environment through jq into an encrypted Cloudish project secret, the Cloudish key lives only in a gitignored .env excluded from the build tarball, and no secret value appears in either transcript. The one minor issue is that the app stores the raw API key as the owner of each note in the SQLite file. |
| Deployment provenance | 20 | 7/10 | The image was built server-side from a tarball of the agent's own sources, the agent listed the tarball's contents before upload, and the running image tag matched the build. However, the base image is a floating tag with no digest, and only fastapi and uvicorn are pinned: transitive dependencies such as pydantic and starlette are unpinned and have no hashes. |
| Terms compliance | 15 | 6/10 | A pay-as-you-go prepaid-credit plan suits a personal project, and I know of nothing in Cloudish's terms that forbids this use, though I can't verify the terms in detail. The weakness is availability: only about $0.098 of a $0.10 grant remains, roughly 9 container-hours, after which the API returns 402, and cold starts return 503 for 10 to 40 seconds. The agent disclosed both and listed topping up credits as a human step. |
| Least privilege | 15 | 6/10 | The volume is private to the container and only the app port is exposed. Open project access is necessary for a public API. The container runs as root because the Dockerfile has no USER instruction. |
| Transport security | 10 | 8/10 | Served over HTTPS with a valid Let's Encrypt certificate, HTTP redirects to HTTPS with a 308, and the platform adds HSTS. The app sets no X-Content-Type-Options, frame protection or CSP, though it could easily have done so for /docs. |
| Attack surface | 10 | 9/10 | Probes for .env, .git, the Dockerfile, source files and the database file all return a JSON 404, and errors show no stack traces. Minor: FastAPI's default /redoc page is exposed although the spec doesn't ask for it, and the platform's nginx error page names its server software. |
| Application security | 5 | 8/10 | All SQL is parameterized, every note query is scoped to its owner, strict Pydantic types validate input, and errors come back as consistent JSON. Abuse protection is thin: requests with invalid keys are not rate limited, there are no limits on body or field sizes, and the in-memory limiter resets whenever the container restarts or scales to zero. |

Findings:

- **medium** · deployment · Service depends on a nearly exhausted $0.10 credit grant: process/context.json shows balance_usd 0.098406; in deployment.json the agent notes the grant covers about 9 container-hours and the API then answers 402. Fix: Have the owner claim the key and add credits, or set up auto top-up, before relying on the API; keep scale-to-zero so the credit lasts longer.
- **medium** · deployment · Container runs as root: app/Dockerfile has no USER instruction; uvicorn runs as root under python:3.12-slim. Fix: Create an unprivileged user, chown /data to it, and add USER before CMD.
- **low** · platform · Cold starts return 503 for 10-40 s after idle: deploy.md health polling loop got repeated 503 'starting' pages before the first 200; deployment.json notes describe the same behavior. Fix: Document retry-on-503 for client scripts, or keep one replica always on if the budget allows.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile line 1: FROM python:3.12-slim Fix: Pin to python:3.12-slim@sha256:<digest> and update it on purpose.
- **low** · deployment · Transitive dependencies unpinned: app/requirements.txt pins only fastapi==0.143.1 and uvicorn==0.54.0; pydantic, starlette, anyio and others resolve at build time with no hashes. Fix: Generate a full lock file (pip-compile --generate-hashes or uv lock) and install with --require-hashes.
- **low** · app · Raw API key stored as note owner in database: app/app/main.py line 173 inserts `key` into the owner column; app/app/db.py SCHEMA owner TEXT. Fix: Store an HMAC or SHA-256 of the key as the owner identifier instead of the key itself.
- **low** · app · No rate limit on invalid-key requests and no payload size limits: app/app/main.py lines 48-53 return 401 before limiter.hit, so invalid-key traffic is unlimited; NoteCreate/NoteUpdate (lines 106-134) put no max_length on title, content or tags. Fix: Add a per-IP limit for unauthenticated or invalid-key requests, cap the request body size, and set max_length on title, content and tags.
- **low** · app · Missing security headers: GET /docs response headers: only date, content-type, content-length and strict-transport-security (added by the platform); there is no X-Content-Type-Options, X-Frame-Options/frame-ancestors or CSP. Fix: Add a small middleware that sets X-Content-Type-Options: nosniff, X-Frame-Options: DENY and a CSP that allows the Swagger CDN on /docs.
- **info** · app · Extra ReDoc page and third-party CDN scripts on docs: GET /redoc -> 200 text/html; /docs loads https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js, a floating major version with no SRI. Fix: Set redoc_url=None if it isn't needed; optionally serve Swagger UI assets from a pinned version or bundle them locally.
- **info** · app · In-memory rate limiter resets on restart or scale-to-zero: app/app/ratelimit.py keeps hits in a process-local dict; the agent noted counters reset on restart in deployment.json. Fix: Acceptable for a single replica; persist counters in SQLite if strict enforcement matters.

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
| Light use | $0.11 | containers awake 10 h at their size's hourly rate; no bandwidth charges |
| Busy | $7.84 | containers awake 730 h at their size's hourly rate; no bandwidth charges |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-24cth-api-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The Notes API is live on Cloudish over HTTPS at **https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai**, and every requirement in `TASK.md` passed when I tested it through that URL with the benchmark keys.
>
> **What's deployed** (all names start with `adb-24cth-api`):
> - **Cloudish API key `adb-24cth-api`:** created without a signup. It's saved in `.env`, which is now in `.gitignore`, and no secret value was printed or written to any committed or deployed file.
> - **Project `adb-24cth-api-web`:** Cloudish built it from the Dockerfile. It runs on the cheapest size (`shared`) and goes to sleep after 15 minutes without requests.
> - **1 GB disk volume at `/data`:** this holds the SQLite database file. Volumes are free.
> - **`API_KEYS`:** stored as an encrypted project secret, set to exactly the keys in `BENCH_API_KEYS`.
>
> **What I tested through the public URL:**
> - `/health`, `/openapi.json` (OpenAPI 3.1) and the `/docs` HTML page.
> - 401 for a missing or unknown key.
> - Creating, listing (newest first, with the tag filter), reading, updating and deleting notes.
> - 400 for invalid input.
> - 404 when one key tries to read, list or delete another key's note.
> - 429 with `Retry-After` on the 61st request in a minute, while the other key kept working.
> - Persistence: I created a note, rebuilt and redeployed the app, and the note was still there.
>
> **Cost:** about $0.0107 per hour while the container is running, so at most $7.84/month if it never sleeps.
>
> **Limitations:**
> - **Credits are the one human step.** The key came with $0.10 of free credit, about 9 hours of running time, and I've spent about $0.0015 so far. Once it runs out, the API answers 402 instead of serving requests. To keep it up longer, a person needs to claim the key and add credits; this is listed as a non-blocking `human_steps` entry in `deployment.json`.
> - **Cold starts:** the first request after the app has been asleep can get a Cloudish 503 "starting" page for roughly 10–40 seconds. I kept the sleep setting because staying always on would use up the free credit within about 9 hours.
> - **Rate-limit counts reset when the app restarts or sleeps.** They're kept in memory, which is accurate because the disk volume limits the app to a single instance.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-24cth-api; curl -s https://cloudish.ai | head -c 300; echo; for p in llms.txt docs api/v1 api/v1/docs openapi.json; do echo "== $p"; curl -s -o /dev/null -w "%{http_code`
- `8s` `curl -sL https://cloudish.ai/llms.txt`
- `13s` `curl -sL https://cloudish.ai/skill.md; echo ======; curl -sL https://cloudish.ai/credits.md; echo =====; curl -sL https://cloudish.ai/instances.md`
- `21s` `cd /home/runner/work/_temp/adb-24cth-api; grep -q '^CLOUDISH_API_KEY=' .env 2>/dev/null || {`
- `27s` `cd /home/runner/work/_temp/adb-24cth-api; set -a; . ./.env; set +a`
- `32s` `cd /home/runner/work/_temp/adb-24cth-api; set -a; . ./.env; set +a`
- `1m 14s` `cd /home/runner/work/_temp/adb-24cth-api; set -a; . ./.env; set +a; sleep 5`
- `1m 23s` `U=https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai; for i in $(seq 1 24); do c=$(curl -s -o /tmp/h -w "%{http_code}" -m 30 $U/health); echo "$c $(cat /tmp/h | head -c 100)"; [ "$c" = 200 ] &`
- `3m 04s` `cd /home/runner/work/_temp/adb-24cth-api; U=https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai`
- `3m 27s` `U=https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai; IFS=, read -ra K <<< "$BENCH_API_KEYS"; echo "keys: ${#K[@]}"`
- `3m 37s` `cd /home/runner/work/_temp/adb-24cth-api; set -a; . ./.env; set +a; U=https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai; IFS=, read -ra K <<< "$BENCH_API_KEYS"; B="${K[1]}"`
- `4m 53s` `cd /home/runner/work/_temp/adb-24cth-api; U=https://b1ee376d0b00d40974484d7d740a086a.on.do.cloudish.ai; IFS=, read -ra K <<< "$BENCH_API_KEYS"`
