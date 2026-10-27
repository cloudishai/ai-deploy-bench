# ✅ API / Backend Service on DigitalOcean with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-j9ibd-api-sqyx2.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $12.00/month, Busy: $12.00/month (the agent estimated $12.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-j9ibd-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 21s | 9m 00s | 12m 26s |
| Turns | 11 | 7 | |
| Tokens | 438.4K | 401.5K | 1.15M |
| Agent cost | $0.45 | $0.33 | $1.01 |
| Shell commands | 10 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 05s, 306.7K tokens, $0.23).

## Screenshots

**The API documentation at /docs** (https://adb-j9ibd-api-sqyx2.ondigitalocean.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Python 3.12
- Frameworks: FastAPI
- Data: PostgreSQL (App Platform dev database)
- Libraries: Uvicorn, psycopg, SQLAlchemy
- Dev tools: HTTPX, pytest
- Packaging: Docker (python:3.12-slim)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 358 lines in 17 files (Python 294, Shell 56, Markdown 43, YAML 27, JSON 12, Docker 8)
- Dependencies: 0 npm, 6 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**87/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Python, FastAPI, SQLAlchemy and PostgreSQL on App Platform suit a small authenticated JSON API with generated docs and persistent storage. The stack is simple and close to its STACK.md rationale, with the dev database as a cost-saving departure from the plan.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | FastAPI generates the required OpenAPI document and /docs page, Pydantic covers validation, and PostgreSQL through SQLAlchemy gives durable storage that survives redeploys. The only limitation is the in-memory rate limiter, which is fine at one instance and is documented. |
| Proportion | 30 | 9/10 | There is one service, one database and four direct dependencies, with no extra caches or queues. The build matches STACK.md, apart from using the cheaper dev database instead of the managed cluster STACK.md describes. |
| Platform fit | 30 | 8/10 | An App Platform container with a bound database and an injected DATABASE_URL uses DigitalOcean's managed path well. Building locally and pushing to DOCR, rather than letting App Platform build from a repository, adds a manual step, and the dev database gives up some of the managed-database benefits. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**81/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.38) of the process, the code, the hosting plan and the live app.

The Notes API is a small, well-built FastAPI service on DigitalOcean App Platform. API keys are stored as an encrypted App Platform secret, it is HTTPS-only with an HTTP redirect, nothing beyond the app is exposed, and input validation and owner isolation are solid. The main weaknesses are that the container runs as root, the dev PostgreSQL database is reachable from the internet, build inputs (base image, transitive dependencies, image reference) are not digest-pinned, and the app sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS is stored as an encrypted App Platform SECRET (resources.json shows an EV[...] value), and DATABASE_URL comes from the database binding. No key appears in the source, the image or the logs. The keys only reach the spec through a mktemp file that is deleted on exit. One minor point: a local .env holds the keys, but .dockerignore keeps it out of the image. |
| Deployment provenance | 20 | 7/10 | The image was built from the reviewed source and pushed to the owner's own DOCR registry, and top-level dependencies are pinned to exact versions. However, the base image is a floating tag with no digest, transitive dependencies have no lock file or hashes, the app spec points at a tag rather than a digest, and /docs loads swagger-ui@5 from a CDN with no pinned version. |
| Terms compliance | 15 | 9/10 | This is a personal side project on a paid DigitalOcean account: a $5 always-on App Platform service plus a $7 dev PostgreSQL database. DigitalOcean's standard terms allow this, and nothing sleeps or expires. The dev database has limited durability guarantees, which is acceptable for personal use. |
| Least privilege | 15 | 6/10 | The container runs as root because the Dockerfile has no USER line. The App Platform dev database cannot be restricted with trusted sources, so it is reachable from the internet, protected only by its credentials. The app also connects as the database owner and creates its schema at startup. |
| Transport security | 10 | 8/10 | The app is served only over HTTPS with a valid Google Trust Services certificate, and HTTP returns a 301 redirect to HTTPS. The app sets none of HSTS, X-Content-Type-Options, X-Frame-Options or CSP, and the platform does not add them either. |
| Attack surface | 10 | 10/10 | Requests for /.env, /.git/config, /Dockerfile, source paths, /admin and /debug all return 404. Errors are JSON with no stack traces, and only the documented public endpoints (/health, /openapi.json, /docs) respond without a key. |
| Application security | 5 | 8/10 | Pydantic strict types validate input, authentication and rate limiting run in middleware before the body is parsed, other keys' notes return 404, and SQLAlchemy queries are parameterized. Minor gaps: no size limits on title, content, tags or the request body, the tag filter loads all of a key's notes into memory, and rate-limit counters live in process memory. |

Findings:

- **medium** · deployment · Container runs as root: app/Dockerfile: FROM python:3.12-slim ... CMD uvicorn ...; there is no USER instruction, so the process runs as uid 0 Fix: Create an unprivileged user (e.g. `RUN useradd -r app` then `USER app`) before CMD.
- **medium** · deployment · Dev database is publicly reachable and cannot use trusted sources: deploy/app.yaml databases: engine PG, production: false; resources.json shows an App Platform dev database. Dev databases do not support trusted-source restrictions, so the endpoint accepts connections from the internet with valid credentials. Fix: Use a managed PostgreSQL cluster attached as a production database with trusted sources limited to the app, or accept the risk explicitly for a personal project.
- **low** · deployment · Base image and transitive dependencies not pinned: app/Dockerfile line 1: `FROM python:3.12-slim` (no @sha256 digest); app/requirements.txt pins only 4 top-level packages, with no lock file or --require-hashes Fix: Pin the base image by digest and install from a hashed lock file (pip-compile --generate-hashes).
- **low** · deployment · Deployment references a mutable image tag: resources.json: image.tag "20261026195955" in DOCR; deploy.sh pushes by tag and does not record the digest in the spec Fix: Reference the image by digest in the app spec (image.digest) so the deployed artifact cannot be swapped.
- **low** · app · Docs page loads unpinned third-party scripts from a CDN: GET /docs returns <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"> with no SRI and a floating major version Fix: Pin the swagger-ui version with SRI, or serve the assets from the app (FastAPI get_swagger_ui_html with custom URLs).
- **low** · app · No security headers: curl -D - https://adb-j9ibd-api-sqyx2.ondigitalocean.app/docs shows no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options or Content-Security-Policy Fix: Add a small middleware that sets HSTS, nosniff, frame-ancestors/X-Frame-Options and a CSP for /docs.
- **low** · app · No size limits on note fields or request bodies: app/app/main.py NoteCreate: title StrictStr min_length=1 with no max_length; content and tags are unbounded; the db.py columns are Text/JSON Fix: Add max_length on title and content, a cap on the number and length of tags, and a request body size limit.
- **low** · app · Rate limiter is in memory and tag filter runs in Python: app/app/ratelimit.py keeps deques in process memory; main.py list_notes loads all of a key's notes and then filters `tag in n.tags` Fix: Move counters to a shared store if the app scales beyond one instance, and filter tags in SQL (JSONB containment).
- **info** · deployment · API keys written to a local .env and a temporary spec file: deploy.md: `umask 077; echo "BENCH_API_KEYS=$BENCH_API_KEYS" > .env`; deploy.sh writes the keys into a mktemp spec that is removed by trap. .dockerignore excludes .env. Fix: This is acceptable. Optionally pass secrets to doctl through stdin or a secret manager rather than files.

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
| app | adb-j9ibd-api | adb-j9ibd-api-web: apps-s-1vcpu-0.5gb x 1, adb-j9ibd-api-db: dev database | $12.00 | adb-j9ibd-api-web: apps-s-1vcpu-0.5gb x 1; adb-j9ibd-api-db: dev database |
| registry | adb-j9ibd-api | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-j9ibd-api-sqyx2.ondigitalocean.app**, and every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What's deployed** (about $12/month):
> - **Web service:** `adb-j9ibd-api-web` on App Platform (app `adb-j9ibd-api`), one instance at the smallest size (`apps-s-1vcpu-0.5gb`), $5/month. HTTPS comes with the default `ondigitalocean.app` address.
> - **Database:** `adb-j9ibd-api-db`, an App Platform dev PostgreSQL 16 database, $7/month.
> - **Container registry:** `adb-j9ibd-api`, free starter tier, holding the Docker image.
> - **API keys:** `API_KEYS` is set to exactly the keys in `BENCH_API_KEYS`, stored as an encrypted secret. `.env` holds only those keys, and no key value appears in any other project file.
>
> **Testing through the public URL:**
> - `deploy/smoke.sh` passed all 15 checks: the three public endpoints, `401` for missing or wrong keys, create/read/list/update/delete, `400` for bad input, the tag filter, `404` for another key's notes, `429` after 60 requests, and the other key still working when one hits its limit.
> - Both benchmark keys are accepted.
> - A note I created was still there after a forced rebuild and redeploy.
>
> **Fixes along the way:**
> - The empty token line I'd left in `.env` would have overridden your token, so I removed it.
> - The first deploy failed because the image tag was read as a number, not text. Quoting it in `deploy/app.yaml` fixed it.
>
> **Limitations:**
> - **Rate-limit counters** are kept in the app's memory, so they reset on every redeploy. The app also has to stay at one instance, or the limit would apply per instance.
> - **No standby database:** the dev database has no backup node. DigitalOcean's separate Managed PostgreSQL ($15/month) would be more durable.
>
> `human_steps` in `deployment.json` is empty, since nothing needed a person this time.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-j9ibd-api; umask 077; echo "BENCH_API_KEYS=$BENCH_API_KEYS" > .env`
- `9s` `cd /home/runner/work/_temp/adb-j9ibd-api; timeout 1500 deploy/deploy.sh 2>&1 | grep -vE 'Pushing|Waiting|Layer already|Preparing|^#' | tail -25`
- `37s` `cd /home/runner/work/_temp/adb-j9ibd-api; sed -i 's/tag: IMAGE_TAG/tag: "IMAGE_TAG"/' deploy/app.yaml; timeout 1500 deploy/deploy.sh 2>&1 | grep -vE 'Pushing|Waiting|Layer already|Preparing|Pushed|^#|`
- `7m 33s` `cd /home/runner/work/_temp/adb-j9ibd-api; ID=ef58a2a5-3083-4537-8f5b-40f9cec37b40; doctl apps list-deployments $ID --format Phase,Progress --no-header | head -2; U=https://adb-j9ibd-api-sqyx2.ondigita`
- `7m 48s` `cd /home/runner/work/_temp/adb-j9ibd-api; U=https://adb-j9ibd-api-sqyx2.ondigitalocean.app; ID=ef58a2a5-3083-4537-8f5b-40f9cec37b40`
- `8m 53s` `cd /home/runner/work/_temp/adb-j9ibd-api; cat > deployment.json <<'EOF'`
