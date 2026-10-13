# ✅ API / Backend Service on Cloudish with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-umu0d-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 09s | 2m 25s | 4m 34s |
| Turns | 9 | 13 | |
| Tokens | 358.3K | 780.3K | 1.14M |
| Agent cost | $0.42 | $0.39 | $0.81 |
| Shell commands | 7 | 12 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `fastapi`, `uvicorn`
- Code: 419 lines in 10 files (Python 409, Markdown 15, JSON 15, Docker 10)
- Dependencies: 0 npm, 5 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-umu0d-api' into a human account (mint a fresh link with GET https://cloudish.ai/api/v1/credi

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.38) of the process, the code, the hosting plan and the live app.

The Notes API is deployed cleanly on Cloudish. Secrets are handled well: the Cloudish key stayed in a local .env file and never left it, and API_KEYS is an encrypted platform secret. The app is served only over HTTPS with HSTS, uses parameterised SQL, enforces per-key ownership, and exposes nothing beyond its documented endpoints. The main weaknesses are that the service runs on a free credit grant that will be used up within about 9 hours (marked non-blocking), the container runs as root, the base image and transitive dependencies aren't pinned, and the app sets none of the extra security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to a chmod-600 .env file without being printed, and that file was left out of the build tarball. API_KEYS was set as an encrypted Cloudish project secret from a temp file that was deleted afterwards, and the app reads it from the environment. No secrets appear in the source, the transcripts or the deployed files. |
| Deployment provenance | 20 | 7/10 | Cloudish built the image on its servers from the agent's own source tarball, and the redeploy reused that exact image tag (builds/89:51e5b650f318). The base image python:3.12-slim is a floating tag rather than a digest, and only top-level dependencies are pinned, with no hashes and no lock for transitive packages. |
| Terms compliance | 15 | 6/10 | A pay-as-you-go plan on prepaid credits suits a personal project, and scale-to-zero with cold starts is acceptable here. However, the unclaimed key only holds the ~$0.1 free grant, about 9 hours of runtime, after which the API returns 402. The agent disclosed this but marked it non-blocking, even though friends' scripts need the API to keep working. |
| Least privilege | 15 | 7/10 | SQLite sits on a private persistent volume, there is no extra public service, and the project's 'open' access is what a public API needs. The container runs as root because the Dockerfile has no USER directive. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Let's Encrypt certificate, HTTP gets a 308 redirect to HTTPS, and the platform adds HSTS. The app doesn't set X-Content-Type-Options, frame protection or CSP, though it easily could have. |
| Attack surface | 10 | 9/10 | Probes for .env, .git, the Dockerfile and source paths all return a uniform 404 JSON response, errors don't leak stack traces, and only the required /docs and /openapi.json are public. The platform's CORS layer reflects any Origin with credentials allowed, which matters little because auth uses a header rather than cookies. |
| Application security | 5 | 8/10 | All SQL is parameterised, ownership is checked on every query, Pydantic validates input strictly, and the per-key rate limit and 401 handling meet the spec. Title, content and tags have no length limits, and requests with invalid keys aren't rate-limited. |

Findings:

- **medium** · deployment · Service is funded only by a free credit grant that runs out in hours: process/context.json balance_usd 0.098983; process/deployment.json human_steps: 'The key only has the free 0.1-credit grant (~9 hours of container runtime at $0.0107/h). Once it runs out the API returns 402' marked "blocking": false Fix: Before handing the API over, claim the key into the owner's account and add credits or set up billing, and treat this as a blocking step.
- **medium** · deployment · Container runs as root: app/Dockerfile has no USER directive; CMD runs uvicorn as the image default (root) Fix: Create an unprivileged user, chown /data to it and add `USER app` before CMD.
- **low** · deployment · Base image and transitive dependencies not pinned: app/Dockerfile line 1 `FROM python:3.12-slim` (tag, not digest); app/requirements.txt pins only fastapi, uvicorn[standard] and pydantic, without hashes, so starlette and uvicorn's extras resolve at build time Fix: Pin the base image by @sha256 digest and install from a fully locked requirements file with --require-hashes.
- **low** · app · Missing security headers: GET https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai/docs returned only content-type, vary, access-control-allow-credentials and strict-transport-security headers, with no X-Content-Type-Options, X-Frame-Options/frame-ancestors or CSP Fix: Add a small middleware that sets X-Content-Type-Options: nosniff, X-Frame-Options: DENY and a restrictive CSP (with an exception for the Swagger UI CDN on /docs).
- **low** · platform · Platform CORS reflects arbitrary origins with credentials: OPTIONS /v1/notes with Origin: https://evil.example -> 204, access-control-allow-origin: https://evil.example, access-control-allow-credentials: true, allow-headers: x-api-key (the app code has no CORS middleware) Fix: Have the platform stop reflecting arbitrary origins with credentials by default, or let apps set their own CORS policy; the impact here is limited because auth uses an X-API-Key header, not cookies.
- **low** · app · No size limits on note fields or tag counts: app/app/main.py lines 161-172: title/content/tags are StrictStr / List[StrictStr] with min_length only, so a valid key can store arbitrarily large notes on the 1 GB volume Fix: Add max_length on title and content, a cap on the number and length of tags, and a request-body size limit.
- **info** · app · Requests with invalid keys are not rate-limited: app/app/main.py lines 241-246: the limiter only runs after the key is validated, so 401 responses are unlimited Fix: Optionally add a per-IP limit on failed authentication to slow down key guessing.
- **info** · app · Rate-limit state in memory resets on scale-to-zero or restart: app/app/main.py lines 136-155 (in-process deque); process/deployment.json notes acknowledge the reset Fix: Acceptable for one replica; store the counters in SQLite or Redis if stronger guarantees are needed.

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
| project | adb-umu0d-api-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The Notes API is live on Cloudish at **https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai**, and every requirement in `TASK.md` works through that URL.
>
> **What's deployed:**
> - **Cloudish key `adb-umu0d-api`:** created through Cloudish's unauthenticated API and saved in `.env`, which is gitignored and was left out of the upload.
> - **Project and app `adb-umu0d-api-web`:** Cloudish built the existing Dockerfile on its own servers. It runs as one copy on the cheapest size (`shared`), which shuts down after inactivity and starts again on the next request.
> - **Database:** the SQLite file sits on a 1 GB persistent disk (volume) at `/data`.
> - **API keys:** `API_KEYS` is set to exactly the keys in `BENCH_API_KEYS`, stored as an encrypted Cloudish secret.
>
> **What I tested through the public URL:**
> - `/health`, `/openapi.json` and `/docs` all return `200`.
> - A missing or wrong key gets `401`.
> - Create, list (including the `tag` filter), get, update and delete all return the right status codes, and bad input gets `400`.
> - One key can't see or delete another key's notes (`404`).
> - The 61st request in a minute gets `429` with `Retry-After`, and the other key keeps working.
> - A note created before a redeploy was still there afterwards.
>
> **Limitations:**
> - **Credits:** the key only has the free grant of 0.1 credits, which covers about 9 hours of running time. When it runs out, the API answers `402` instead of serving requests. I listed claiming the key and adding credits as a non-blocking item in `human_steps`.
> - **Cost:** the estimate in `deployment.json` is $7.84/month, which assumes the app is always on. Real cost should be lower because it shuts down when idle, but the first request after a quiet period will be slower.
> - **Rate limit:** the per-minute counts are kept in memory, so they reset whenever the app restarts or shuts down when idle.
>
> Nothing else failed. All details are in `deployment.json`.

## Shell commands during deploy

- `4s` `curl -sL https://cloudish.ai/skill.md > /tmp/skill.md; wc -l /tmp/skill.md; sed -n 1,160p /tmp/skill.md; echo "BENCH set: ${BENCH_API_KEYS:+yes}"; ls -A`
- `6s` `sed -n 160,363p /tmp/skill.md; curl -sL https://cloudish.ai/instances.md | head -60`
- `11s` `R=$(curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"agent":"claude-code","alias":"adb-umu0d-api"}') && K=$(echo "$R" | python3 -c 'import sys,json;print(json.`
- `17s` `source .env && tar --exclude='.env*' --exclude='.git' --exclude='.venv' --exclude='data' --exclude='.pytest_cache' --exclude='__pycache__' --exclude='context.tar.gz' -czf /tmp/context.tar.gz . && tar `
- `22s` `source .env && python3 -c 'import json,os;print(json.dumps({"name":"API_KEYS","value":",".join(k.strip() for k in os.environ["BENCH_API_KEYS"].split(",") if k.strip())}))' > /tmp/sec.json && curl -s -`
- `56s` `source .env && curl -s https://cloudish.ai/api/v1/projects/adb-umu0d-api/adb-umu0d-api-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.`
- `1m 00s` `source .env && curl -s https://cloudish.ai/api/v1/projects/adb-umu0d-api/adb-umu0d-api-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | head -c 3000; echo; curl -s https://cloudish.ai/api/v1/images/`
- `1m 10s` `cat > /tmp/remote_test.sh <<'EOF'`
- `1m 18s` `U=https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai; K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1 | xargs); K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2 | xargs)`
- `1m 33s` `source .env && curl -s -X POST https://cloudish.ai/api/v1/projects -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d '{"name":"adb-umu0d-api-web","image":"registry.do`
- `2m 03s` `U=https://159168c2ef42f208d2c7d6594d843d63.on.do.cloudish.ai; K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2 | xargs); curl -s -w " [%{http_code}]\n" -H "X-API-Key: $K2" $U/v1/notes/a52c9ec1b4914e14b829dc1`
- `2m 17s` `cat > deployment.json <<'EOF'`
