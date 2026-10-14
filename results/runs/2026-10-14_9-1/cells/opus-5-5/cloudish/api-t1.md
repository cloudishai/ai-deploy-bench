# ✅ API / Backend Service on Cloudish with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-hcgq7-api.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-hcgq7-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 3m 09s | 3m 54s | 7m 02s |
| Turns | 20 | 16 | |
| Tokens | 744.0K | 1.10M | 1.85M |
| Agent cost | $0.66 | $0.52 | $1.17 |
| Shell commands | 11 | 15 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-hcgq7-api.on.do.cloudish.ai/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: —
- Code: 672 lines in 12 files (JavaScript 664, JSON 27, Markdown 20, Docker 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key adb-hcgq7-api and add credits (mint a fresh link with GET https://cloudish.ai/api/v1/credits/clai

## Security and compliance review

**77/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.37) of the process, the code, the hosting plan and the live app.

The Notes API is built and deployed cleanly. API_KEYS is held as a Cloudish secret, the Cloudish credential never left the local .env, the image Cloudish built from the uploaded code is what runs, the code has no dependencies, HTTPS is enforced, and nothing beyond the API is exposed. The main weaknesses: the container runs as root, the base image tag isn't pinned, and the app runs on an unclaimed free credit grant that lasts only about 9 running hours before it stops serving, which doesn't fit an API friends need to stay up. There are also minor gaps in security headers and abuse controls.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS is stored as a Cloudish project secret and read from the environment. The Cloudish API key stayed in a local .env that was left out of the build context and never printed. One small issue: the raw API key is stored in plaintext as the note owner in SQLite. |
| Deployment provenance | 20 | 8/10 | Cloudish built the image server-side from a context the agent uploaded, and the running app uses that build's image (builds/95:f01db1a3752a). The app has no dependencies, but the base image node:24-slim is a floating tag and isn't pinned by digest. |
| Terms compliance | 15 | 5/10 | Personal use fits an unclaimed free Cloudish key, as far as I know its terms, but I'm not certain of them. The 0.1 credit grant covers only about 9 running hours. After that the app returns 402 until a person claims the key and adds credit, so a service friends rely on won't stay up. The agent disclosed this but marked it non-blocking. |
| Least privilege | 15 | 6/10 | The container runs as root: the agent deliberately removed `USER node` from the Dockerfile. The SQLite database is on a private volume, and the only public resource is the HTTPS endpoint the app needs. |
| Transport security | 10 | 8/10 | Served over TLS 1.3 with a valid Let's Encrypt certificate. HTTP gets a 308 redirect to HTTPS, and the platform adds HSTS. The app sets no X-Content-Type-Options, frame protection or CSP, which it could have done. |
| Attack surface | 10 | 10/10 | Probes for .env, .git, source files, the Dockerfile, debug and admin paths, and path traversal all got a JSON 404. Malformed input got clean JSON errors with no stack traces. |
| Application security | 5 | 8/10 | Input is validated strictly, every query is parameterized and scoped to the owner, other keys get 404s, and the per-key rate limit works. Requests with invalid keys aren't rate-limited, and nothing caps note count or total storage per key. |

Findings:

- **medium** · deployment · App runs on an unclaimed free credit grant that runs out in about 9 hours: process/deployment.json human_steps: 'The free grant (~0.1 credits) only covers about 9 running hours ... When the balance reaches zero the app stops serving (402)'; deploy.md line 281 runway: runningHoursLeft 9.2; context.json balance_usd 0.098476 Fix: Have the owner claim the key and fund it, or set up auto top-up, before the API is handed to the friends who will call it. Treat this as a blocking step.
- **medium** · deployment · Container runs as root: process/build.md line 100: sed -i '/chown/d;/USER node/d' Dockerfile; app/Dockerfile has no USER directive Fix: Restore `RUN mkdir -p /data && chown node:node /data` and `USER node`, or use the platform's volume fsGroup/ownership options.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile line 1: FROM node:24-slim Fix: Pin the base image as node:24-slim@sha256:<digest> and update it on purpose.
- **low** · app · Missing security headers: curl -sI https://adb-hcgq7-api.on.do.cloudish.ai/health returns only content-type, content-length and strict-transport-security (HSTS comes from the platform); no X-Content-Type-Options, X-Frame-Options or CSP. app/src/app.js send() sets only Content-Type and Content-Length Fix: Send X-Content-Type-Options: nosniff, a restrictive CSP and frame-ancestors 'none' on every response, especially /docs.
- **low** · app · Raw API keys stored in plaintext as the note owner: app/src/db.js line 55: stmts.insert.run(id, owner, ...) with owner = the X-API-Key value (app/src/app.js line 111: store.create(key, input)) Fix: Store an HMAC or SHA-256 hash of the key, or a key ID, as the owner, so a leaked database file doesn't reveal valid credentials.
- **low** · app · Invalid-key requests aren't rate-limited and storage per key is unbounded: app/src/app.js lines 87-90: the 401 for an unknown key is returned before limiter.hit(); MAX_BODY_BYTES is 1 MiB (line 5), and there is no cap on note count or field length, against a 1 GB volume Fix: Add a per-IP limit for failed authentication, and cap field lengths and notes per key.
- **info** · app · No sensitive files or debug endpoints exposed: GET /.env, /.git/config, /package.json, /src/app.js, /Dockerfile, /debug and /admin all return 404 {"error":"Not found"}; POST /v1/notes with malformed JSON and a bad key returns 401 {"error":"Invalid API key"} Fix: None.
- **info** · platform · HTTPS enforced with a valid certificate: curl -I http://adb-hcgq7-api.on.do.cloudish.ai/health -> 308 to https; TLSv1.3, CN=adb-hcgq7-api.on.do.cloudish.ai, issuer Let's Encrypt YR2, expires Jan 12 2027; strict-transport-security: max-age=31536000 Fix: None.

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
| project | adb-hcgq7-api | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The Notes API is live on Cloudish at **https://adb-hcgq7-api.on.do.cloudish.ai**, over HTTPS with a valid certificate. I tested every requirement in `TASK.md` through that URL and all of them passed.
>
> **What's deployed**
> - **Cloudish account:** I created a Cloudish API key named `adb-hcgq7-api` myself, which needed no sign-up. It's saved in `.env`, which was left out of the upload.
> - **App:** a project named `adb-hcgq7-api`, built by Cloudish from the Dockerfile. It runs on the cheapest size (`shared`) as a single instance on port 8080.
> - **Database:** SQLite in a 1 GB persistent volume mounted at `/data`. Volumes are free.
> - **API keys:** `API_KEYS` is set as an encrypted Cloudish secret, equal to `BENCH_API_KEYS` (2 keys).
> - **Cost:** about $7.84/month if it ran all the time. It's billed only while running, and I set it to sleep after 1 hour without requests, so the real cost will be lower.
>
> **Tested through the public URL**
> - **No-auth endpoints:** `/health`, `/openapi.json` and `/docs` all return 200 without a key.
> - **Auth:** missing and wrong keys both get 401.
> - **Notes:** create, read, update and delete all work.
> - **Validation:** an empty title, wrong types and invalid JSON each get 400.
> - **Ownership and listing:** one key can't see or change another key's notes (404), the list is newest first, and `?tag=` filtering works.
> - **Rate limit:** past 60 requests a minute, one key got 429 with a `Retry-After` header while the other key kept working.
>
> **Not fully verified or limited**
> - **Persistence on Cloudish:** I couldn't force a real container restart there. Redeploying the same image left the running container alone, and an environment-variable change I sent wasn't applied. Notes are written to the persistent volume, and surviving a restart was confirmed locally with Docker.
> - **Wake-up delay:** after an hour without requests, the first request gets a "starting up" page with status 503 for about 10–20 seconds while the app wakes.
> - **Rate-limit counters** are kept in memory, so they reset whenever the app restarts or wakes up.
>
> **Needs a person, but nothing is blocked yet:** the free credit covers only about 9 running hours. When it runs out, the app stops serving until someone claims the key and adds credit. This is listed under `human_steps` in `deployment.json`, with how to get a claim link (each link expires after 30 minutes).

## Shell commands during deploy

- `3s` `curl -sL https://cloudish.ai/skill.md -o /tmp/skill.md; wc -l /tmp/skill.md; cat /tmp/skill.md; ls -la; echo "BENCH set: ${BENCH_API_KEYS:+yes}"`
- `8s` `npm test 2>&1 | grep -E "^ℹ (pass|fail)" && curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"agent":"claude-code","alias":"adb-hcgq7-api"}' > /tmp/key.json && `
- `13s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude='node_modules' --exclude='data' -czf /tmp/context.tar.gz . && tar -tzf /tmp/context.tar.gz && curl -s -X POST https://c`
- `18s` `set -a && . ./.env && set +a && python3 -c "import json,os;print(json.dumps({'name':'API_KEYS','value':os.environ['BENCH_API_KEYS']}))" | curl -s -o /dev/null -w "secret %{http_code}\n" -X PUT https:/`
- `53s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/projects/adb-hcgq7-api/adb-hcgq7-api -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c "`
- `55s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/projects/adb-hcgq7-api/adb-hcgq7-api -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -m json.tool | grep -v -i secret | head -`
- `58s` ❌ `set -a && . ./.env && set +a && curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-hcgq7-api/adb-hcgq7-api/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json`
- `1m 05s` ❌ `for i in $(seq 1 12); do r=$(curl -s -m 30 -w " %{http_code}" https://adb-hcgq7-api.on.do.cloudish.ai/health 2>&1); echo "$r"; case "$r" in *200) break;; esac; sleep 10; done; curl -sv -m 20 https://a`
- `1m 52s` `set -a && . ./.env && set +a && curl -s -X PATCH https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d '{"settings":{"idleTimeoutSeconds":36`
- `2m 01s` `cd /tmp && B=https://adb-hcgq7-api.on.do.cloudish.ai K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1) K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2) && echo "nkeys=$(echo "$BENCH_API_KEYS" | tr ',' '\n' | wc -l`
- `2m 10s` `B=https://adb-hcgq7-api.on.do.cloudish.ai K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1) K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2); for i in $(seq 1 62); do curl -s -o /dev/null -w "%{http_code}\n" $B/v1`
- `2m 30s` `set -a && . ./.env && set +a && curl -s -X POST https://cloudish.ai/api/v1/projects -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d '{"name":"adb-hcgq7-api","image"`
- `2m 54s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/docker/adb-hcgq7-api/adb-hcgq7-api/logs -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c "import sys,json;print(json.load(sy`
- `3m 02s` `set -a && . ./.env && set +a && curl -s -o /dev/null -w "%{http_code}\n" -X POST https://cloudish.ai/api/v1/projects -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d`
- `3m 45s` `cat > deployment.json <<'EOF'`
