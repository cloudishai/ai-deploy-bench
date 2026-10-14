# ✅ API / Backend Service on DigitalOcean with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-eeen0-api-x7cct.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $12.00/month, Busy: $12.00/month (the agent estimated $12.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-eeen0-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 41s | 9m 52s | 12m 33s |
| Turns | 11 | 9 | |
| Tokens | 460.7K | 482.7K | 943.4K |
| Agent cost | $0.53 | $0.37 | $0.90 |
| Shell commands | 10 | 8 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-eeen0-api-x7cct.ondigitalocean.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Express
- Data: PostgreSQL (App Platform dev database)
- Libraries: node-postgres
- Dev tools: SuperTest
- Packaging: Docker (node:22-alpine), App spec (.do/app.yaml)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 522 lines in 13 files (JavaScript 512, JSON 33, YAML 31, Markdown 26, Docker 10)
- Dependencies: 3 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**82/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.34) of the process, the code, the hosting plan and the live app.

The Notes API is well built: secrets come from App Platform's encrypted secret mechanism, the container runs as non-root, the database connection uses verified TLS, queries are parameterized, ownership is enforced, and the live site exposes nothing beyond the API, with HTTPS enforced. The main weakness is provenance: the image was built locally and pushed under the mutable tag v1, from an unpinned base image, with no source-controlled pipeline. Smaller gaps are missing security headers and a dev database that can't be firewalled and has no backups.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS is stored as an encrypted App Platform SECRET and DB credentials come from bindable variables, so nothing is baked into the image or source. The only small issue is that the deploy step wrote the real keys into a temporary spec file in /tmp (deleted right after) and left a 30-day registry login on the runner. |
| Deployment provenance | 20 | 6/10 | The image was built from the agent's local workspace and pushed to a registry the account owns, with npm ci against a lockfile. But there is no git source, the base image node:22-alpine and the deployed tag v1 are mutable rather than pinned by digest, and doctl was downloaded without verifying its checksum. |
| Terms compliance | 15 | 9/10 | This is a personal project on paid App Platform Basic plus a dev Postgres database, which fits DigitalOcean's standard terms; nothing sleeps or expires. The dev database has no backups and DigitalOcean doesn't recommend it for production, which is acceptable here. The account plan couldn't be read, so this is judged from standard terms. |
| Least privilege | 15 | 8/10 | The container runs as the non-root node user, there is one public service, and DB TLS is verified against the CA. The App Platform dev database can't be restricted to trusted sources, so it is reachable from the internet with credentials (as I understand the platform). |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. Neither the app nor the spec sets HSTS, X-Content-Type-Options, frame protection or CSP. |
| Attack surface | 10 | 9/10 | Probes for .env, .git, source files, admin and debug paths all return a JSON 404. Errors don't include stack traces, and only the endpoints the spec requires are public. The platform adds an x-do-app-origin header. |
| Application security | 5 | 9/10 | Queries are parameterized, each note is scoped to a SHA-256 hash of its owner's key, input types and lengths are checked, docs output is HTML-escaped, and the per-key rate limit works. Minor gaps: key lookup isn't constant-time, and failed-auth and public endpoints aren't throttled by the app. |

Findings:

- **medium** · deployment · Image built from local workspace with mutable tags, no source-controlled pipeline: process/deploy.md: `docker build -q -t registry.digitalocean.com/adb-eeen0-api/adb-eeen0-api-web:v1 . && docker push ...`; resources.json image tag "v1" (no digest); no github/git source in the spec Fix: Deploy from a git repository the owner controls (App Platform github source or CI), and reference the image by digest or use immutable, unique tags.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile:1 `FROM node:22-alpine` Fix: Pin the base image, e.g. `FROM node:22-alpine@sha256:<digest>`, and update it deliberately.
- **low** · deployment · Deploy tool downloaded without checksum verification: process/deploy.md: `curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/` Fix: Check the release checksum file (or use a pinned, verified action or package) before installing.
- **low** · deployment · Real API keys written to a temporary spec file; long-lived registry login: process/deploy.md: heredoc writes `value: "$BENCH_API_KEYS"` into /tmp/adb-spec.yaml (removed after `doctl apps create`); `doctl registry login` -> 'Login valid for 30 days' Fix: Set the secret after creation via a placeholder plus `doctl apps update` from a protected file, or use a short-lived spec with restrictive permissions, and use `--expiry-seconds` for the registry login.
- **low** · platform · Dev database can't be locked to trusted sources: resources.json: databases [{name: adb-eeen0-api-db, engine: PG}] with no production cluster; App Platform dev databases don't support trusted sources/VPC restriction Fix: If the data matters, move to a managed PostgreSQL cluster with trusted sources limited to the app (plus backups).
- **low** · app · No security headers: curl -sD - https://adb-eeen0-api-x7cct.ondigitalocean.app/health and /docs: no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options or Content-Security-Policy Fix: Add helmet (or set the headers manually) in src/app.js, at least HSTS, nosniff, frame-ancestors 'none' and a restrictive CSP for /docs.
- **info** · deployment · Dev database has no backups or standby: process/deployment.json notes: 'It has no backups or standby node' Fix: Accept for a personal project, or upgrade to a managed cluster with daily backups if the notes need protecting.
- **info** · app · Non-constant-time key check; failed auth not throttled: app/src/app.js: `if (!key || !keys.has(key)) return next(new HttpError(401, ...))` runs before the limiter, which only counts valid keys Fix: Compare hashed keys and add a lightweight per-IP limit on 401 responses and the public endpoints.
- **info** · platform · Platform adds an origin identifier header: GET /health response header `x-do-app-origin: a729f523-3b2d-41bb-aaf6-a3724a89d61c` Fix: No action needed; this is App Platform's default behavior.

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
| app | adb-eeen0-api | adb-eeen0-api-web: apps-s-1vcpu-0.5gb x 1, adb-eeen0-api-db: dev database | $12.00 | adb-eeen0-api-web: apps-s-1vcpu-0.5gb x 1; adb-eeen0-api-db: dev database |
| registry | adb-eeen0-api | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The API is live at **https://adb-eeen0-api-x7cct.ondigitalocean.app**, and every requirement in TASK.md worked when I tested it through that URL.
>
> **What's deployed:**
> - **Web service:** a DigitalOcean App Platform app (`adb-eeen0-api`) running one Basic instance (`apps-s-1vcpu-0.5gb`), about $5/month. It runs the Docker image I built and pushed to a free DigitalOcean Container Registry (`adb-eeen0-api`).
> - **Database:** a PostgreSQL 16 dev database (`adb-eeen0-api-db`) attached to the app, about $7/month. The app connects to it over an encrypted, certificate-checked connection.
> - **API keys:** `API_KEYS` is set to the keys from `BENCH_API_KEYS` and stored as an encrypted secret in the app.
>
> The total is about **$12/month**.
>
> **What I tested through the public URL:**
> - `/health`, `/openapi.json` and `/docs` return 200.
> - A missing or wrong API key gets 401.
> - Create, list, tag filter, get, update and delete all return the right responses. Bad input gets 400.
> - Another key gets 404 on a note it doesn't own.
> - After 60 requests in a minute, one key gets 429 with a `Retry-After` header, while the other key still gets 200.
> - A note I created was still there after a forced redeploy, so the data persists.
>
> **Limitations:**
> - **Rate limiting:** the counters are kept in the app's memory. The app has to stay at one instance, and the counters reset whenever it restarts or redeploys.
> - **Database:** the dev database has no backups or standby copy. A full managed PostgreSQL database (about $15/month) would add those.
> - **Updates:** deploys don't run automatically from git. To change the app, push a new image to the registry and redeploy.
>
> Nothing needed a person, so `human_steps` is empty. I didn't create any credentials, so there's no `.env`. The resource IDs and these notes are in `deployment.json`.

## Shell commands during deploy

- `6s` `which doctl; echo "keys: $(echo -n "$BENCH_API_KEYS" | tr ',' '\n' | wc -l)"; curl -s -H "Authorization: Bearer $DIGITALOCEAN_ACCESS_TOKEN" https://api.digitalocean.com/v2/account | python3 -c 'import`
- `14s` `cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ && doctl version && doctl registry creat`
- `30s` `docker build -q -t registry.digitalocean.com/adb-eeen0-api/adb-eeen0-api-web:v1 . && docker push -q registry.digitalocean.com/adb-eeen0-api/adb-eeen0-api-web:v1 && echo "API_KEYS_SET_FROM=BENCH_API_KE`
- `45s` `doctl apps create --spec /tmp/adb-spec.yaml --wait --format ID,DefaultIngress,Phase 2>&1 | tail -3; rm -f /tmp/adb-spec.yaml`
- `7m 14s` `doctl apps list -o json | python3 -c 'import sys,json;[print(a["id"],a.get("default_ingress"),a.get("active_deployment",{}).get("phase"),a.get("last_deployment_active_at")) for a in json.load(sys.stdi`
- `7m 27s` `B=https://adb-eeen0-api-x7cct.ondigitalocean.app; K1=$(echo "$BENCH_API_KEYS"|cut -d, -f1); K2=$(echo "$BENCH_API_KEYS"|cut -d, -f2); J='Content-Type: application/json'`
- `7m 41s` `B=https://adb-eeen0-api-x7cct.ondigitalocean.app; sleep 60; K1=$(echo "$BENCH_API_KEYS"|cut -d, -f1)`
- `9m 44s` `cat > deployment.json <<'EOF'`
