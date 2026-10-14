# ✅ Database-Backed CRUD App on Cloudish with Opus 5.5 (trial 1)

**success**: 18/19 checks passed (95%).

- URL: https://adb-n8x1p-crud-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-n8x1p-crud`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 23s | 6m 16s | 8m 38s |
| Turns | 11 | 19 | |
| Tokens | 508.5K | 1.27M | 1.77M |
| Agent cost | $0.56 | $0.61 | $1.16 |
| Shell commands | 10 | 18 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 562 lines in 9 files (JavaScript 382, HTML 172, JSON 47, Docker 8, Markdown 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish API key 'adb-n8x1p-crud' and add credits: run `curl https://cloudish.ai/api/v1/credits/claim -H "Auth

## Security and compliance review

**74/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.39) of the process, the code, the hosting plan and the live app.

The app is well built and nothing sensitive is exposed: no leaked secrets, scrypt and hashed tokens, parameterized SQL, verified per-user isolation and CSRF protection, and HTTPS-only serving with HSTS. The biggest problem is the hosting: a commercial app is running on an unclaimed key with a 0.1-credit free grant that will run out in hours and take the app offline. Smaller issues are a root container, an unpinned base image deployed from an unversioned local tarball, no rate limiting on login and signup, and missing security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The only credential, the Cloudish API key, was written straight to a chmod-600 .env file without being printed, was excluded from the build tarball and .gitignore, and never appears in source or deployed files. The app itself needs no secrets. |
| Deployment provenance | 20 | 7/10 | The Cloudish builder built the image from the agent's own Dockerfile and a local tarball, and the app has zero npm dependencies. But the base image is a floating tag (node:24-slim) rather than a digest, and the deployed source isn't tied to any versioned commit or repository. |
| Terms compliance | 15 | 4/10 | This is a commercial app running on an unclaimed API key that isn't tied to any account and has a 0.1-credit free grant (balance $0.093, about 8.7 running hours). It will stop serving with 402/503 once the grant runs out. The agent disclosed this but marked it non-blocking. Paid prepaid credits are probably fine for commercial use, but I can't confirm Cloudish's terms for unclaimed keys. |
| Least privilege | 15 | 6/10 | SQLite sits on a private persistent volume with no public data store, and public 'open' access is appropriate for a web app. However, the container runs as root because the Dockerfile has no USER directive. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Let's Encrypt certificate. HTTP gets a 308 redirect to HTTPS, and the platform adds HSTS. The app sets its own headers but omits X-Content-Type-Options, frame protection and CSP. |
| Attack surface | 10 | 9/10 | No source files, .env, .git, database or directory listings are reachable. Unknown paths return a JSON 404 with no stack traces. The only extras are a harmless /healthz and the platform's nginx-branded error pages. |
| Application security | 5 | 7/10 | Solid basics: scrypt password hashing, SHA-256-hashed random tokens, parameterized SQL, textContent rendering, per-user ownership checks, a CSRF guard for cookie auth, and body and length limits. The main gap is that login and signup have no rate limiting, which allows credential guessing and CPU exhaustion through scrypt on a 0.1-CPU instance. |

Findings:

- **high** · deployment · Commercial app runs on an unclaimed free-credit key that will run out within hours: process/deployment.json: plan "unclaimed key, 0.1 free credits"; human_steps.why: "about 8.7 running hours left ... At a zero balance the app stops serving (402/503)"; process/context.json: use "commercial", balance_usd 0.092756. Fix: Claim the key into the business's Cloudish account and add paid credits (or enable auto top-up) before going live. Treat this as blocking for a commercial app, and confirm that the account's terms allow commercial use.
- **medium** · deployment · Container runs as root: app/Dockerfile: FROM node:24-slim ... CMD ["node", "server.js"] with no USER directive, so the process runs as UID 0. Fix: Add `USER node` (and chown /data to that user, or use the platform's volume ownership options) so the app runs as an unprivileged user.
- **medium** · app · No rate limiting on login and signup: app/server.js:193-220: the signup and login handlers run scrypt (N=16384) on every request, with no per-IP or per-account throttling. The service is the 'shared' 0.1-CPU plan. Fix: Add per-IP and per-account attempt limits with backoff on /api/auth/login and /api/auth/signup, or use platform-level rate limiting if Cloudish offers it.
- **low** · deployment · Base image not pinned to a digest: app/Dockerfile:1 `FROM node:24-slim` Fix: Pin the base image by digest (node:24-slim@sha256:...) and update it on purpose.
- **low** · deployment · Deployed from an ad-hoc local tarball, not versioned source: process/deploy.md: `tar ... -czf /tmp/context.tar.gz . && curl -X POST https://cloudish.ai/api/v1/projects ... -F "context=@/tmp/context.tar.gz"`. The project directory is not a git repo, and the tarball was deleted afterward (`rm -f /tmp/context.tar.gz`). Fix: Commit the source to an owner-controlled repository and deploy from a tagged commit, so the running image can be traced back to its source.
- **low** · app · Missing security headers (nosniff, frame protection, CSP): curl -D - https://adb-n8x1p-crud-web.on.do.cloudish.ai/ returns only content-type, cache-control and strict-transport-security (HSTS comes from the platform). The app writes its own headers in server.js:76 and :188 but sets none of these. Fix: Set X-Content-Type-Options: nosniff, a frame-ancestors 'none' CSP or X-Frame-Options: DENY, and a restrictive Content-Security-Policy on the HTML response.
- **info** · platform · Platform nginx error pages reveal server software: TRACE / returns 405 with an HTML page '<center>nginx</center>'. GET /%2e%2e/server.js returns 400 with an nginx-branded page. Fix: Platform-level; nothing for the app to do. Cloudish could serve neutral error pages.
- **info** · platform · HTTPS correctly enforced: http://adb-n8x1p-crud-web.on.do.cloudish.ai/ returns 308 with Location: https://...; the certificate is CN=adb-n8x1p-crud-web.on.do.cloudish.ai, issued by Let's Encrypt YR2, valid until Jan 12 2027; strict-transport-security: max-age=31536000. Fix: None.
- **info** · app · Authorization and CSRF checks verified live: PATCH /api/todos/1 with a fresh user's bearer token returns 404 'Todo not found'. A cookie-authenticated POST /api/todos with Origin https://evil.example and Sec-Fetch-Site: cross-site returns 403. The cookie is set with HttpOnly; SameSite=Lax; Secure. Fix: None.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the web app as HTML | yes | passed |  |
| POST /api/auth/signup creates an account and returns a token | yes | passed |  |
| Signup rejects an invalid email and a short password with 400 | yes | passed |  |
| Signing up twice with the same email returns 409 | yes | passed |  |
| POST /api/auth/login returns a token | yes | passed |  |
| Login with a wrong password returns 401 | yes | passed |  |
| /api/todos requires a valid token (401) | yes | passed |  |
| POST /api/todos creates a todo | yes | passed |  |
| An empty title is rejected with 400 | yes | passed |  |
| GET /api/todos lists the caller's todos | yes | passed |  |
| Todos are listed oldest first | no | passed |  |
| PATCH /api/todos/{id} renames and completes a todo | yes | passed |  |
| Users can't see or modify each other's todos (404) | yes | passed |  |
| DELETE /api/todos/{id} removes a todo | yes | passed |  |
| Data is still there a minute later, with a fresh login | yes | passed |  |
| The web UI renders a login or signup form | no | failed | TimeoutError: Page.goto: Timeout 30000ms exceeded. Call log:   - navigating to "https://adb-n8x1p-crud-web.on.do.cloudish.ai/", waiting until "networkidle"  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.11 | containers awake 10 h at their size's hourly rate; no bandwidth charges |
| Busy | $7.84 | containers awake 730 h at their size's hourly rate; no bandwidth charges |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-n8x1p-crud-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The app is live at **https://adb-n8x1p-crud-web.on.do.cloudish.ai**, and every requirement in `TASK.md` works through that URL.
>
> **What's deployed**
> - **API key:** I created a Cloudish API key named `adb-n8x1p-crud` (it comes with 0.1 free credits). The key is saved in `.env`, which is excluded from git and from the build.
> - **App:** project `adb-n8x1p-crud-web`, built by Cloudish from the Dockerfile on its smallest size (`shared`). It sleeps when idle and is billed per second only while running.
> - **Database:** SQLite on a 1 GB persistent Cloudish volume mounted at `/data`.
> - **Cost:** about $7.84/month if it ran around the clock. Volumes are free, so with light use the cost is much lower (about $0.41/month at an hour a day).
>
> **How I tested it through the public URL**
> - **API:** I used curl to run every endpoint and every error code (400, 401, 404, 409, 204). I also checked that todos come back oldest first, and that a second user can't see, edit or delete the first user's todos.
> - **Web UI:** I ran it in a headless Chrome browser: sign up, add, complete and uncomplete, rename, delete, reload, log out, a failed login, then a successful one.
> - **Persistence:** a todo created before two redeploys was still there afterwards.
>
> **One bug, now fixed:** Cloudish's proxy rewrites the `Host` header. That made my check against forged cross-site requests reject the web UI's own requests with a 403. I changed the check to use a header the browser sets itself (`Sec-Fetch-Site`), marked the login cookie Secure, added a test for this, and redeployed. The browser run above was against the fixed version.
>
> **Needs a person (not blocking yet):** the free credits cover about 8.7 more hours of running time. When they run out, the app stops serving until someone claims the key and adds credits. To do that, mint a claim link with the command in `deployment.json` and open it. The link expires 30 minutes after it's created. This is listed under `human_steps`.
>
> **Other limitations:**
> - The first request after an idle period takes a few seconds while the app starts.
> - Because it uses a volume, the app always runs as a single copy.

## Shell commands during deploy

- `3s` `cd /home/runner/work/_temp/adb-n8x1p-crud; ls -A; curl -sL https://cloudish.ai/skill.md | tail -c +15000 | head -c 8000; echo; curl -sL https://cloudish.ai/instances.md | head -c 4000`
- `8s` `cd /home/runner/work/_temp/adb-n8x1p-crud; R=$(curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"agent":"claude-code","alias":"adb-n8x1p-crud"}'); echo "$R" | j`
- `11s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a`
- `16s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a`
- `1m 21s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a; sleep 5`
- `1m 30s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a`
- `1m 40s` `cd /tmp; B=https://adb-n8x1p-crud-web.on.do.cloudish.ai; J='content-type: application/json'; E="t$(date +%s)@example.com"`
- `1m 46s` ❌ `curl -sv https://adb-n8x1p-crud-web.on.do.cloudish.ai/healthz 2>&1 | tail -15; dig +short adb-n8x1p-crud-web.on.do.cloudish.ai; curl -s -o /dev/null -w "%{http_code}\n" https://c3a0aca641a00d700c947dd`
- `1m 50s` `for i in $(seq 1 30); do a=$(curl -s -o /dev/null -w "%{http_code}" https://adb-n8x1p-crud-web.on.do.cloudish.ai/healthz); echo "$i $a"; [ "$a" = 200 ] && break; sleep 10; done`
- `2m 10s` `B=https://adb-n8x1p-crud-web.on.do.cloudish.ai; J='content-type: application/json'; E="t$(date +%s)@example.com"; O=$(mktemp)`
- `2m 21s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a`
- `3m 19s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a; B=https://adb-n8x1p-crud-web.on.do.cloudish.ai; sleep 15`
- `3m 48s` `cd /home/runner/work/_temp/adb-n8x1p-crud; python3 - <<'EOF'`
- `3m 58s` `cd /home/runner/work/_temp/adb-n8x1p-crud; cat >> test/api.test.js <<'EOF'`
- `5m 36s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i -s playwright@1 >/dev/null 2>&1 && npx playwright install --with-deps chromium >/dev/null 2>&1; echo rc=$?`
- `5m 52s` `cd /home/runner/work/_temp/adb-n8x1p-crud; set -a; . ./.env; set +a; B=https://adb-n8x1p-crud-web.on.do.cloudish.ai`
- `6m 05s` `cd /home/runner/work/_temp/adb-n8x1p-crud; cat > deployment.json <<'EOF'`
- `6m 08s` `cd /home/runner/work/_temp/adb-n8x1p-crud; sed -i 's/about \$0.33\/month at 1 h\/day/about $0.41\/month at 1 h\/day/' deployment.json; grep -o 'about \$0.41[^,]*' deployment.json`
