# ⚠️ API / Backend Service on DigitalOcean with Opus 5.5 (trial 1)

**partial** (failed at verify): 19/20 checks passed (95%).

- URL: https://adb-r8zod-api-dwfel.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $12.00/month, Busy: $12.00/month (the agent estimated $12.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-r8zod-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 44s | 8m 07s | 10m 50s |
| Turns | 12 | 8 | |
| Tokens | 511.3K | 429.9K | 941.2K |
| Agent cost | $0.55 | $0.35 | $0.91 |
| Shell commands | 11 | 7 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-r8zod-api-dwfel.ondigitalocean.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `express`, `pg`
- Code: 574 lines in 13 files (JavaScript 564, JSON 32, YAML 31, Markdown 23, Docker 10)
- Dependencies: 3 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**84/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.32) of the process, the code, the hosting plan and the live app.

The Notes API was built and deployed carefully. API keys live in an encrypted App Platform SECRET, nothing leaked into logs, files or the image, the container runs as non-root, the database uses CA-verified TLS, and the live app exposes only the specified endpoints with clean JSON errors over valid HTTPS. The weaknesses are minor: the base image and deployed tag aren't pinned by digest, the image was built and pushed from a local machine, there are no security headers, failed-auth attempts aren't rate limited, and the dev database can't be restricted to trusted sources.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS is stored as an encrypted App Platform SECRET env var, and DB credentials and the CA come from platform bindings. Keys were never echoed, written to source or baked into the image. The temporary spec holding them was written under umask 077 and then deleted. The only nit is a 30-day registry login left on the build host. |
| Deployment provenance | 20 | 7/10 | The image was built from the reviewed source with npm ci and a lockfile, and pushed to the owner's own DOCR registry. The base image (node:22-alpine) and the deployed image tag (v1) are mutable and not pinned by digest, and the doctl binary was downloaded without checksum verification. |
| Terms compliance | 15 | 9/10 | This is a personal side project on a paid Basic App Platform service with a paid dev Postgres database. As far as I know, DigitalOcean's terms don't restrict personal use and nothing here sleeps or expires. The dev database has no backups or HA, which is acceptable for this use. |
| Least privilege | 15 | 8/10 | The container runs as the non-root node user, the database is an App Platform-managed attached database used over CA-verified TLS, and only the HTTP service is public. Dev databases can't be restricted with trusted sources, so the DB endpoint is likely reachable from the internet, guarded only by its credentials (I'm not certain of DigitalOcean's current dev-DB network model). |
| Transport security | 10 | 8/10 | HTTPS uses a valid Google Trust Services certificate and HTTP returns 301 to HTTPS. Responses carry no HSTS, X-Content-Type-Options, frame protection or CSP, and the app could have set these itself. |
| Attack surface | 10 | 10/10 | Only the specified endpoints respond. Probes for .env, .git, package.json, source and admin/debug paths return a JSON 404, errors are generic JSON without stack traces, and x-powered-by is disabled. |
| Application security | 5 | 8/10 | Queries are parameterized, input is type- and length-checked, notes are scoped by a hashed key owner (other keys get 404), the docs HTML is escaped and per-key rate limiting works. Failed-auth attempts aren't rate limited, and the limiter is in memory only. |

Findings:

- **low** · deployment · Base image and deployed image tag not pinned by digest: app/Dockerfile:1 `FROM node:22-alpine`; app/.do/app.yaml image `tag: v1` (mutable tag in DOCR) Fix: Pin the base image to node:22-alpine@sha256:<digest>, and deploy by an immutable tag or digest per build (e.g. the git SHA).
- **low** · deployment · Deploy CLI downloaded without integrity verification: process/deploy.md:4 `curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/` Fix: Verify the release checksum (doctl-1.146.0-checksums.sha256) before installing, or use a package manager or pinned action.
- **low** · deployment · Image built and pushed from a local workstation rather than from a tracked source: process/deploy.md:24 `docker build ... && docker push registry.digitalocean.com/adb-r8zod-api/adb-r8zod-api-api:v1`; there's no repository or CI linkage in the app spec Fix: Build from a version-controlled repo (App Platform git source or CI) so the running image can be traced to a commit.
- **low** · platform · Dev database can't be restricted to trusted sources: process/resources.json: databases `adb-r8zod-api-db` engine PG as an App Platform dev database (app/.do/app.yaml `production: false`) Fix: For stronger isolation, use a managed database cluster with trusted sources limited to the app (or VPC). This is acceptable for a personal project.
- **low** · app · No security headers (HSTS, nosniff, frame protection, CSP): curl -sD - https://adb-r8zod-api-dwfel.ondigitalocean.app/health and curl -sI /docs: headers contain only content-type, etag, cache-control and Cloudflare headers; no strict-transport-security, x-content-type-options, x-frame-options or content-security-policy Fix: Add helmet (or set the headers manually) in src/app.js, including HSTS and a restrictive CSP for /docs.
- **low** · app · Unauthenticated / invalid-key requests are not rate limited: app/src/app.js:89-93 returns 401 before limiter.check(key) runs, so invalid-key guesses are unlimited Fix: Apply a per-IP limit to failed authentication attempts (keys should also be long and random).
- **info** · app · In-memory rate limiter resets on restart and won't scale across instances: app/src/rateLimit.js:4 `const hits = new Map()`; acknowledged in process/deployment.json notes Fix: Back the limiter with a shared store (Redis or Postgres) if the service is scaled out.
- **info** · deployment · Registry login credentials left on the build host for 30 days: process/deploy.md:24 `doctl registry login` -> 'Notice: Login valid for 30 days' Fix: Use `doctl registry login --expiry-seconds 600` or log out after pushing.

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
| Notes are private to the API key that created them | yes | failed | GET /v1/notes/426b46a1-73ce-4d8e-b632-8ec85e31e180 returned 429, expected 404 or 403: {"error":"Rate limit exceeded; retry in 23 seconds"} |
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
| app | adb-r8zod-api | adb-r8zod-api-api: apps-s-1vcpu-0.5gb x 1, adb-r8zod-api-db: dev database | $12.00 | adb-r8zod-api-api: apps-s-1vcpu-0.5gb x 1; adb-r8zod-api-db: dev database |
| registry | adb-r8zod-api | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-r8zod-api-dwfel.ondigitalocean.app**, and I tested every requirement in `TASK.md` through that URL.
>
> **What's running (about $12/month):**
> - **Container registry** `adb-r8zod-api`, on the free starter tier. It holds the app's Docker image.
> - **App** `adb-r8zod-api` on DigitalOcean App Platform, running one instance of the smallest paid size ($5/month). HTTPS comes on the default `ondigitalocean.app` address.
> - **Database** `adb-r8zod-api-db`, an App Platform PostgreSQL 16 "dev database" ($7/month). This was cheaper than a standalone managed Postgres database (about $15/month).
> - **API keys:** `API_KEYS` is set to exactly the keys in `BENCH_API_KEYS`, stored as an encrypted secret. The key values aren't in any file; the temporary config file that held them during deployment has been deleted.
>
> **Results through the public URL:**
> - `/health`, `/openapi.json` and `/docs` each return 200.
> - A missing or unknown key gets 401.
> - Create, read, update, delete and the `tag` filter all work, and an empty title gets 400.
> - Another key's note gets 404.
> - A note was still there after I forced a full rebuild and redeploy.
> - A burst of 62 requests from one key started getting 429s after the limit, with a `Retry-After` header.
>
> **Limitation:** the rate-limit counts are held in the server's memory. That's exact with the single instance, but the counts reset whenever the app restarts or redeploys, and running several instances would make it a limit per instance.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty. I didn't create any new credentials, so `.env` is empty. I also updated `.do/app.yaml` to deploy from the registry image instead of a GitHub repo; to ship a code change, push a new image tag and update it in that file.

## Shell commands during deploy

- `6s` `which doctl || (cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/); doctl version; doctl a`
- `12s` `doctl registry create adb-r8zod-api --subscription-tier starter --region nyc3 && doctl registry login && docker build -q -t registry.digitalocean.com/adb-r8zod-api/adb-r8zod-api-api:v1 . && docker pus`
- `50s` `cat > .do/app.yaml <<'EOF'`
- `59s` `A=8a789613-c40b-450e-8f92-87050f396990; for i in $(seq 1 40); do P=$(doctl apps get $A -o json | python3 -c 'import json,sys;a=json.load(sys.stdin)[0];print((a.get("active_deployment") or {}).get("pha`
- `6m 35s` `B=https://adb-r8zod-api-dwfel.ondigitalocean.app; K1=$(echo $BENCH_API_KEYS|cut -d, -f1); K2=$(echo $BENCH_API_KEYS|cut -d, -f2)`
- `6m 45s` `A=8a789613-c40b-450e-8f92-87050f396990; B=https://adb-r8zod-api-dwfel.ondigitalocean.app; K2=$(echo $BENCH_API_KEYS|cut -d, -f2)`
- `8m 00s` `cat > deployment.json <<'EOF'`
