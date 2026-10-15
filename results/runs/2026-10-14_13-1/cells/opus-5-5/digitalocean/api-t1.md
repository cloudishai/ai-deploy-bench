# ✅ API / Backend Service on DigitalOcean with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-5e3ks-api-omhxz.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $12.00/month, Busy: $12.00/month (the agent estimated $12.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-5e3ks-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 59s | 8m 55s | 13m 00s |
| Turns | 11 | 11 | |
| Tokens | 449.7K | 677.4K | 1.51M |
| Agent cost | $0.52 | $0.45 | $1.21 |
| Shell commands | 10 | 10 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 06s, 378.2K tokens, $0.24).

## Screenshots

**The API documentation at /docs** (https://adb-5e3ks-api-omhxz.ondigitalocean.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Python 3.12
- Frameworks: FastAPI
- Data: PostgreSQL (App Platform dev database)
- Libraries: Uvicorn, psycopg, SQLAlchemy
- Dev tools: HTTPX, pytest
- Packaging: Docker (python:3.12-slim), App spec (.do/app.yaml)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 449 lines in 16 files (Python 387, Shell 52, Markdown 48, YAML 29, JSON 11, Docker 10)
- Dependencies: 0 npm, 6 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

### Stack fit

**87/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Python/FastAPI with SQLAlchemy Core on App Platform plus an attached Postgres dev database is a well-proportioned, idiomatic fit for a small authenticated JSON API, and STACK.md explains the choice soundly. The build matches the documented decision.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | FastAPI with Pydantic provides validation, the OpenAPI 3 document and docs out of the box, and Postgres is a durable store that survived a redeploy. The in-memory rate limiter is correct for the single instance it runs on. Storing tags as a JSON text column and filtering by tag in Python works but is not ideal. |
| Proportion | 30 | 9/10 | The stack is minimal: one service, one database and four direct dependencies, with no extra cache or queue. SQLite is used only for local tests. |
| Platform fit | 30 | 8/10 | It uses App Platform's managed TLS, health checks, encrypted secrets and the database binding that injects DATABASE_URL. The agent built the image locally and pushed it to DOCR instead of letting App Platform build from a repo, which works but skips the platform's own build pipeline. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**82/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.38) of the process, the code, the hosting plan and the live app.

The Notes API is a small, cleanly built FastAPI service on paid DigitalOcean App Platform with an attached Postgres dev database. API keys are stored as an encrypted platform secret, the container runs as non-root, it is served only over HTTPS, and probing found no exposed files, debug endpoints or stack traces. The remaining weaknesses are minor: the base image and transitive dependencies are not pinned, security headers are missing, the dev database is internet-reachable, and malformed bodies get 400 before the auth check, so unauthenticated requests are never rate-limited.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS is stored as an encrypted App Platform SECRET (EV[...] in the live spec) and DATABASE_URL is a platform binding. The spec template uses a placeholder, keys are injected into a temp file that is deleted afterwards, and no secret shows up in the transcripts or the source. The only small weakness is that the plaintext keys sit briefly in a temp spec file on the deploy machine. |
| Deployment provenance | 20 | 7/10 | The agent built the image from the reviewed source, pushed it to the owner's own DOCR registry, and pointed the spec at that unique timestamp tag. Direct dependencies are version-pinned, but the base image python:3.12-slim is not pinned by digest, transitive dependencies (pydantic, starlette) are unlocked, and there are no hashes. The spec references a tag, not an image digest. |
| Terms compliance | 15 | 9/10 | The app is personal and runs on paid DigitalOcean App Platform ($5 basic instance) with a $7 dev database, both of which allow this use and stay up without sleeping. A dev database has limited capacity and no managed backups or HA, which is acceptable for a small side project but worth knowing about. |
| Least privilege | 15 | 7/10 | The container runs as a non-root user, only the one web service is public, and the registry is private. The App Platform dev database cannot be limited to trusted sources, so it is reachable from the internet (protected by TLS and credentials). The app connects as the database owner and runs create_all at startup. |
| Transport security | 10 | 8/10 | HTTP returns 301 to HTTPS, and the certificate is valid (Google Trust Services, expires Dec 2026). The responses carry no HSTS, X-Content-Type-Options, frame protection or CSP headers. Neither the app nor the platform sets them. |
| Attack surface | 10 | 9/10 | Paths such as /.env, /.git/config, source paths, /admin, /debug and /redoc all return JSON 404s. A catch-all handler stops stack traces from leaking, and only the documented public endpoints exist. The Dockerfile copies only the app package. |
| Application security | 5 | 8/10 | Pydantic strict types and length limits validate input, SQLAlchemy Core parameterizes queries, and every query is scoped by owner, so other keys get 404. Each valid key is rate-limited to 60 requests per minute. However, body validation runs before the auth dependency, so unauthenticated requests get 400 instead of 401 and are never rate-limited. Keys are compared without constant-time comparison, and there is no per-key storage quota. |

Findings:

- **low** · deployment · Base image and transitive dependencies not pinned: app/Dockerfile:1 `FROM python:3.12-slim` (no @sha256 digest); app/requirements.txt pins only fastapi, uvicorn, sqlalchemy and psycopg, with no lockfile or --require-hashes; the spec references a tag (resources.json image.tag 20261014234806), not a digest Fix: Pin the base image by digest, generate a fully locked requirements file with hashes (pip-compile --generate-hashes), and reference the image by digest in the app spec.
- **low** · platform · Dev database is publicly reachable and has no trusted-source restriction: app/.do/app.yaml databases: `production: false` (App Platform dev database); dev databases cannot have trusted sources configured, so the endpoint is reachable from the internet and protected only by TLS and credentials Fix: For stronger isolation, use a managed database cluster with trusted sources limited to the app (or VPC). Optionally use a least-privileged role for the app.
- **low** · app · No security headers (HSTS, nosniff, frame protection, CSP): GET https://adb-5e3ks-api-omhxz.ondigitalocean.app/health and /docs: response headers include only content-type, server: cloudflare, cache-control: private, cf-* and alt-svc. There is no strict-transport-security, x-content-type-options, x-frame-options or content-security-policy. Fix: Add a small middleware that sets HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY and a restrictive CSP (especially for the /docs HTML page).
- **low** · app · Body validation runs before authentication; unauthenticated requests are not rate-limited: POST /v1/notes with `X-API-Key: bogus` and body `{bad` returned `HTTP/2 400 {"error":"1: JSON decode error"}` instead of 401. app/app/main.py:122-131 checks the key and rate limit only inside the dependency, which runs after body parsing, and 401s are never counted. Fix: Do API-key checks (and an IP-based limit for failed auth) in middleware before body parsing, so unauthenticated callers always get 401 and cannot hammer the endpoint for free.
- **info** · app · API key compared without constant-time comparison, and no per-key storage quota: app/app/main.py:124-125 `x_api_key not in valid` (set membership); app/app/db.py has no limit on the number of notes per owner (each note can be up to 100,000 chars of content) Fix: Compare keys with hmac.compare_digest, and cap notes per key so a leaked key cannot fill the 512 MB-class dev database.
- **info** · app · Rate limiter is in-memory and per instance: app/app/ratelimit.py:12-13 keeps hits in a process-local dict; deployment.json notes say to keep instance_count at 1. Limits reset on every redeploy or restart. Fix: Acceptable at one instance. Move to a shared store (e.g. Managed Valkey) or Postgres if the app ever scales out.
- **info** · deployment · Dev database has limited durability guarantees: process/deployment.json: `PostgreSQL 16 (App Platform dev database ...) plan: dev database (production: false)` Fix: For a personal side project this is fine. Upgrade to a managed cluster if friends' data needs backups and point-in-time recovery.

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
| Light use | $12.00 | fixed monthly prices; 0.0373 GiB out of a 50 GiB allowance |
| Busy | $12.00 | fixed monthly prices; 49 GiB out of a 50 GiB allowance |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| app | adb-5e3ks-api | adb-5e3ks-api-web: apps-s-1vcpu-0.5gb x 1, adb-5e3ks-api-db: dev database | $12.00 | adb-5e3ks-api-web: apps-s-1vcpu-0.5gb x 1; adb-5e3ks-api-db: dev database |
| registry | adb-5e3ks-api | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-5e3ks-api-omhxz.ondigitalocean.app**, and every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What's deployed (about $12/month):**
> - **Web service:** App Platform app `adb-5e3ks-api` (ID `45f53cd7-e62a-42f5-8066-1b0679a77ab8`), smallest size (`apps-s-1vcpu-0.5gb`, $5/month), one instance. HTTPS comes with App Platform's default address.
> - **Database:** PostgreSQL 16 as an App Platform dev database (`adb-5e3ks-api-db`, $7/month), attached to the app.
> - **Image registry:** `adb-5e3ks-api`, free starter tier.
> - **Keys:** `API_KEYS` is stored as an encrypted secret and set to exactly the keys in `BENCH_API_KEYS`.
>
> **What I checked through the public URL:**
> - `/health`, `/openapi.json` (OpenAPI 3.1) and the HTML `/docs` page all return 200.
> - A missing or unknown key gets `401`.
> - Creating, listing (including the tag filter), reading, updating and deleting notes all return the right status codes, and bad input gets `400`.
> - The second key gets `404` on the first key's note.
> - Over the limit, the first key got `429` with `Retry-After` while the second key still got `200`.
> - A note created before a redeploy was still there afterwards.
>
> **Problems along the way, all fixed:**
> - The first deploy failed because the image tag in `.do/app.yaml` needed quotes.
> - `/openapi.json` didn't list itself in its own document, so I added it and redeployed.
> - For a few seconds right after a deploy, DigitalOcean's front end returned 521 errors twice. It worked normally after that.
>
> **Limitation:** the rate limit is counted in the app's memory. It resets on each redeploy and only works correctly with one instance, so the instance count should stay at 1.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty. I didn't create any new credentials, so `.env` wasn't needed. To redeploy, run `./deploy.sh`; to test, run `./smoke.sh <url>`.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-5e3ks-api; doctl account get --format Email,Status,DropletLimit 2>&1 | sed 's/[^ ]*@[^ ]*/<email>/'; doctl registry get 2>&1 | head -3; doctl apps list 2>&1 | head; doct`
- `17s` `cd /home/runner/work/_temp/adb-5e3ks-api; ./deploy.sh 2>&1 | grep -vE '^#|Pushed|Waiting|Preparing|Layer already|^[a-f0-9]{12}:' | tail -25`
- `49s` `cd /home/runner/work/_temp/adb-5e3ks-api; sed -i 's/tag: __TAG__/tag: "__TAG__"/' .do/app.yaml; ./deploy.sh 2>&1 | grep -E 'APP_ID|URL|Error|rror' | tail -10`
- `6m 22s` `cd /home/runner/work/_temp/adb-5e3ks-api; U=https://adb-5e3ks-api-omhxz.ondigitalocean.app; ./smoke.sh $U; doctl apps logs 45f53cd7-e62a-42f5-8066-1b0679a77ab8 adb-5e3ks-api-web --type run 2>&1 | tail`
- `6m 30s` `cd /home/runner/work/_temp/adb-5e3ks-api; doctl apps logs 45f53cd7-e62a-42f5-8066-1b0679a77ab8 adb-5e3ks-api-web --type run 2>&1 | grep -vE '"GET /health' | tail -30 | cut -c1-250`
- `6m 35s` `cd /home/runner/work/_temp/adb-5e3ks-api; U=https://adb-5e3ks-api-omhxz.ondigitalocean.app; K="X-API-Key: ${BENCH_API_KEYS%%,*}"`
- `6m 42s` `cd /home/runner/work/_temp/adb-5e3ks-api; U=https://adb-5e3ks-api-omhxz.ondigitalocean.app; ./smoke.sh $U`
- `6m 57s` `cd /home/runner/work/_temp/adb-5e3ks-api; python3 - <<'EOF'`
- `8m 12s` `cd /home/runner/work/_temp/adb-5e3ks-api; U=https://adb-5e3ks-api-omhxz.ondigitalocean.app; A="X-API-Key: ${BENCH_API_KEYS%%,*}"`
- `8m 48s` `cd /home/runner/work/_temp/adb-5e3ks-api; cat > deployment.json <<'EOF'`
