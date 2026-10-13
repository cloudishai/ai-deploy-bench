# ✅ Static Content Site on Cloudish with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-l0oek-static-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: $21.66/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-l0oek-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 18s | 3m 38s | 4m 56s |
| Turns | 6 | 11 | |
| Tokens | 185.1K | 541.0K | 726.0K |
| Agent cost | $0.25 | $0.27 | $0.52 |
| Shell commands | 4 | 9 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 282 lines in 13 files (JavaScript 173, HTML 88, JSON 24, CSS 13, Docker 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish API key 'adb-l0oek-static' (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the k

## Security review

**83/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.29) of the process, the code and the live app.

The Northwind Robotics site is a small, dependency-free Node server running as a non-root user. It serves only allowlisted routes over valid HTTPS with an HTTP redirect and HSTS, and the API key was kept out of the build context and every deployed file. The weaknesses are minor: no CSP or frame-protection headers, no rate limiting on /api/contact, a base image not pinned to a digest, and a platform CORS layer that echoes back any origin.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to .env without being echoed, and both the upload tarball (--exclude='.env*') and .dockerignore leave it out. The app itself needs no secrets, and no credential shows up in the source, the image or any live response. |
| Deployment provenance | 15 | 7/10 | The agent's own local sources were uploaded as a tarball and built server-side from the Dockerfile in app/, and there are no npm dependencies. The base image node:22-alpine is a floating tag, not pinned to a digest. |
| Transport security | 15 | 6/10 | HTTPS uses a valid Let's Encrypt certificate, HTTP gets a 308 redirect to HTTPS, and HSTS is set. There is no Content-Security-Policy and no frame protection (X-Frame-Options or frame-ancestors), and the JSON responses lack nosniff. |
| Attack surface | 15 | 9/10 | The server answers only on an allowlist of routes, so source files, .env, .git, Dockerfile and TASK.md all return 404, and path traversal is rejected. The only extras are a harmless /healthz endpoint and a platform-level CORS layer that echoes back any Origin with credentials allowed. |
| Application security | 20 | 8/10 | Input is validated strictly for type, email format and non-empty fields. Bodies over 64 KB get a 413, bad JSON gets a clean 400, and the client renders messages with textContent, so there is no XSS path. /api/contact has no rate limiting or per-field length limits, and it accepts cross-origin submissions. |
| Least privilege | 10 | 9/10 | The container runs as the non-root 'node' user, there is no data store or volume, and only one service is public, which this public site needs. The API key is an unclaimed anonymous account. |

Findings:

- **low** · Missing Content-Security-Policy and frame protection headers: curl -sI https://adb-l0oek-static-web.on.do.cloudish.ai/ returns only content-type, x-content-type-options, strict-transport-security, vary and access-control-allow-credentials, with no CSP or X-Frame-Options. server.js:37-40 sets only Content-Type, Content-Length and X-Content-Type-Options. Fix: Add Content-Security-Policy: default-src 'self'; frame-ancestors 'none' (and/or X-Frame-Options: DENY) and Referrer-Policy in send().
- **low** · No rate limiting on the contact endpoint: 15 back-to-back POST /api/contact requests all returned 200. server.js:42-66 has no throttling, and every valid submission is logged (server.js:63). Fix: Add per-IP rate limiting (for example a token bucket in memory) and per-field length limits for name, email and message.
- **low** · Platform CORS echoes back any Origin with credentials allowed: OPTIONS /api/contact with Origin: https://evil.example returned access-control-allow-origin: https://evil.example, access-control-allow-credentials: true and allow-methods GET,HEAD,PUT,PATCH,POST,DELETE. The app sets no CORS headers, so the platform ingress adds them. The impact is limited because the app uses no cookies or auth. Fix: Turn off or restrict CORS at the platform if it allows that. Otherwise check the Origin in /api/contact and reject foreign origins.
- **low** · Base image not pinned to a digest: app/Dockerfile:1 FROM node:22-alpine Fix: Pin the base image to a digest, e.g. node:22-alpine@sha256:..., and update it on purpose.
- **info** · JSON API responses lack X-Content-Type-Options: server.js:32-35 sendJson sets only Content-Type and Content-Length. The POST /api/contact response headers have no x-content-type-options. Fix: Add X-Content-Type-Options: nosniff in sendJson as well.
- **info** · API key handled correctly: deploy.md: the key is written to .env through a python one-liner without being printed, the tar uses --exclude='.env*', and app/.dockerignore lists .env. Fix: None needed. If the platform supports it, consider claiming or rotating the key once the credits have been added.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / returns HTML | yes | passed |  |
| GET /about returns HTML | yes | passed |  |
| GET /contact returns HTML | yes | passed |  |
| Home has an <h1> containing 'Northwind Robotics' | yes | passed |  |
| About has a heading containing 'About' | yes | passed |  |
| Contact has a form with name, email and message fields | yes | passed |  |
| Every page has a <title> and a viewport meta tag | no | passed |  |
| Home links to /about and /contact | no | passed |  |
| POST /api/contact with valid input returns {ok: true} | yes | passed |  |
| POST /api/contact rejects a bad email and an empty message with 400 | yes | passed |  |
| Unknown paths return 404 | yes | passed |  |
| Submitting the /contact form in a browser posts to /api/contact without leaving the page | yes | passed |  |
| Pages load in a browser without uncaught JavaScript errors | no | passed |  |

## Cloud resources

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-l0oek-static-web | small | $21.66 | 0.5 CPU / 1 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The Northwind Robotics site is live at **https://adb-l0oek-static-web.on.do.cloudish.ai**, and everything in `TASK.md` works through that URL. The catch is credits: it's running on a free grant of only 0.1 credits, so it will stop serving once that runs out unless someone adds more.
>
> **What I deployed**
> - I created a Cloudish API key named `adb-l0oek-static` through the API; no signup was needed. The key is saved in `.env`, and I added `.env` to `.gitignore`.
> - Cloudish built the existing Dockerfile on its own servers and deployed it as one container app, `adb-l0oek-static-web` (project id 82). It uses the default shared size and shuts down after a period with no traffic.
> - I gave it a readable subdomain in place of the random one it was assigned.
>
> **What I tested through the public URL**
> - `/`, `/about` and `/contact` return 200 `text/html`, each with a `<title>`, the viewport tag and links to the other pages.
> - The home page has the "Northwind Robotics" `<h1>`, and the contact page has the `name`, `email` and `message` fields and a submit button.
> - Unknown paths, and the pages with an `.html` suffix, return 404.
> - `POST /api/contact` returns 200 `{"ok":true}` for valid input. It returns 400 with an error for a missing name, an invalid email or an empty message.
> - In a headless Chrome test, submitting the contact form showed the confirmation without reloading the page.
>
> **What didn't go smoothly**
> - **Credits:** the balance after deploying was about 0.097 credits. At most $7.84 a month if it ran all day; actual cost will be lower because it shuts down when idle. When the credits run out, visitors get a 402 or 503 page. Adding more requires a person to claim the key and add credits, which I listed under `human_steps` in `deployment.json`. That step isn't blocking yet.
> - **First request after a quiet spell:** because the app shuts down when idle, that first request can take a few seconds while it starts.
> - **Initial start:** the cluster reported it was short on capacity when the app first started. It came up on its own within about a minute.

## Shell commands during deploy

- `14s` `curl -s https://www.cloudish.ai/skill.md`
- `18s` `ls -a; printf '.env\ncontext.tar.gz\nnode_modules\n' > .gitignore`
- `22s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude='context.tar.gz' -czf /tmp/context.tar.gz . && curl -s -X POST https://cloudish.ai/api/v1/projects -H "Authorization: B`
- `26s` `. ./.env && for i in $(seq 40); do s=$(curl -s https://cloudish.ai/api/v1/images/builds/220 -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import sys,json;b=json.load(sys.stdin)["build"];p`
- `1m 22s` `. ./.env && curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-l0oek-static/adb-l0oek-static-web/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d '{"la`
- `2m 53s` `U=https://adb-l0oek-static-web.on.do.cloudish.ai; for p in / /about /contact /style.css /contact.js /nope /about.html; do curl -s -o /tmp/b -w "$p %{http_code} %{content_type}\n" $U$p; done; curl -s $`
- `3m 03s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i -s puppeteer-core >/dev/null 2>&1; CH=$(which google-chrome chromium chromium-browser 2>/dev/null | head -1); echo $CH; cat > t.js <<'`
- `3m 22s` `. ./.env && curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import sys,json;d=json.load(sys.stdin);k=d.get("apiKey",d);print({x:k.get(x) for x in ("ali`
- `3m 30s` `cat > deployment.json <<'EOF'`
