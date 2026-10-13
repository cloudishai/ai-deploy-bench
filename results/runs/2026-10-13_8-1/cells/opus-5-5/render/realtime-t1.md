# ✅ Real-Time Collaborative App on Render with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-p9gs9-realtime-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-p9gs9-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 49s | 2m 34s | 5m 23s |
| Turns | 14 | 10 | |
| Tokens | 580.8K | 538.3K | 1.12M |
| Agent cost | $0.53 | $0.28 | $0.81 |
| Shell commands | 11 | 9 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-p9gs9-realtime-web.onrender.com/?room=bench-6045a66c)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `pg`, `ws`
- Code: 569 lines in 9 files (JavaScript 427, HTML 142, JSON 29, Markdown 20, YAML 18)
- Dependencies: 2 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**68/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.35) of the process, the code, the hosting plan and the live app.

The chat app itself is well built: input is validated, SQL is parameterized, the UI renders safely, nothing sensitive is exposed, and HTTPS is enforced. No secrets leaked. The biggest weakness is provenance: Render builds from a third-party example repo, and the real code arrives as an opaque tarball in a secret file. The free Postgres, which is likely reachable from the internet, expires on 2026-11-12, after which the app will fail to start. Security headers and rate limiting are also missing.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The Render API key and database credentials never appear in the transcripts, source, or the uploaded bundle. DATABASE_URL is a Render service environment variable, and the bundle (built with git archive from an explicit file list) leaves out .env. Minor points: the connection string was set as a literal env var rather than a fromDatabase link, and the external connection string sits in a local .env file. |
| Deployment provenance | 20 | 4/10 | The live service's recorded source is a third-party public repo (render-examples/express-hello-world, unpinned branch main). The real code arrives as an opaque base64 tarball in a Render secret file and is unpacked by a custom build command. What runs can't be traced to any owner-controlled repo or commit. Dependencies are locked with package-lock.json and npm ci, but the Node version is pinned only to the major version. |
| Terms compliance | 15 | 6/10 | Render's free tier is fine for a personal hobby-club app. However, the free Postgres the app depends on expires on 2026-11-12. After that, store.init() will fail at startup and the service will stop working. Spin-down after 15 minutes idle also drops live WebSocket sessions. Both limits were disclosed but not addressed. |
| Least privilege | 15 | 6/10 | The service runs on Render's managed native runtime and the app reads only what it needs. The Postgres database was created through the API without an ipAllowList. Render's default is to accept external connections from any IP (password-protected), even though the app only needs the internal URL. |
| Transport security | 10 | 7/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP returns 301 to HTTPS. The app sets no HSTS, X-Content-Type-Options, frame protection, or CSP, even though it writes its own response headers and could have. |
| Attack surface | 10 | 9/10 | Requests for .env, .git/config, source files, the secret bundle and other paths return the app's JSON 404. Errors are generic, with no stack traces. Only /healthz is extra, and it returns {"ok":true}. |
| Application security | 5 | 6/10 | Input validation is solid: text, user and room lengths are checked, the body is capped at 16 KB, WebSocket payloads at 64 KB, SQL is parameterized, and the UI renders with textContent, so there is no XSS. However, the public endpoints have no rate limiting or connection caps. The per-room cache never evicts, and the WebSocket upgrade doesn't check the Origin header. |

Findings:

- **high** · deployment · Production built from a third-party example repo with code injected through a secret file: process/deploy.md service creation: "repo":"https://github.com/render-examples/express-hello-world","branch":"main" with buildCommand 'base64 -d /etc/secrets/app.b64 > /tmp/app.tgz; find . -mindepth 1 -maxdepth 1 ! -name app.b64 -exec rm -rf {} +; tar xzf /tmp/app.tgz; npm ci --omit=dev'; process/resources.json source = render-examples/express-hello-world Fix: Push the app to an owner-controlled Git repo, or deploy a digest-pinned image from an owner-controlled registry, and have Render build from that pinned commit. Don't route code through secret files under someone else's repo.
- **medium** · deployment · Free Postgres expires in 30 days and the app fails to start without it: process/resources.json expires_at 2026-11-12T23:32:51Z; app/store.js lines 13-32: init() runs CREATE TABLE against DATABASE_URL and server.js main() exits on error Fix: Use a paid Postgres plan (Basic) or a persistent alternative. At minimum, fall back to memory or degrade gracefully when the database is gone.
- **medium** · deployment · Postgres likely reachable from the internet: process/deploy.md: POST /v1/postgres body has no ipAllowList. Render's default allows external connections from 0.0.0.0/0. The app uses only internalConnectionString. Fix: Set the database ipAllowList to an empty list (internal-only), or restrict it to the specific admin IPs needed.
- **low** · platform · Free web service spins down when idle: process/deployment.json notes: 'sleeps after about 15 minutes idle ... open WebSockets are dropped' Fix: Use the Starter plan if the club needs the chat to be always available.
- **low** · app · No security headers: GET https://adb-p9gs9-realtime-web.onrender.com/?room=general returns only content-type, cache-control, and the platform's rndr-id/server/cf headers. There is no strict-transport-security, x-content-type-options, x-frame-options/frame-ancestors, or content-security-policy (server.js lines 80-84, 113). Fix: Add HSTS, X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none', and Referrer-Policy in sendJson and the index response.
- **low** · deployment · Runtime version only loosely pinned: process/deploy.md envVars NODE_VERSION="22"; app/package.json engines node >=20 Fix: Pin an exact Node version (for example 22.x.y) through NODE_VERSION or .node-version.
- **low** · app · No rate limiting or connection caps on public endpoints: app/server.js lines 136-149 (POST messages), 151-172 (SSE) and 191-200 (WS upgrade) have no per-client limits. app/store.js line 18: the cache Map gets one entry for every room name requested and never evicts. Fix: Add per-IP rate limits on posting and connections, cap concurrent SSE/WS connections, and bound or LRU-evict the room cache.
- **low** · app · WebSocket upgrade doesn't check the Origin header: app/server.js lines 191-200: handleUpgrade is called without looking at req.headers.origin Fix: Accept upgrades only from the app's own origin.
- **info** · deployment · DB connection string copied as a literal env var; TLS verification disabled: process/deploy.md: envVars DATABASE_URL value = ci["internalConnectionString"]; app/store.js line 19: ssl { rejectUnauthorized: false } Fix: Use fromDatabase or an env group link so credentials rotate with the database, and verify TLS when connecting externally.
- **info** · app · No sensitive files or debug endpoints exposed: GET /.env, /.git/config, /package.json, /server.js, /app.b64 and /etc/secrets/app.b64 each return 404 {"error":"not found"}. A malformed path returns a generic Cloudflare 400. Fix: None needed.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the chat UI as HTML | yes | passed |  |
| deployment.json declares a supported transport (websocket or sse) | no | passed |  |
| Clients connect over websocket | yes | passed |  |
| A message reaches another client in the same room within 5 s | yes | passed |  |
| The sender receives its own message too | no | passed |  |
| Messages never reach clients in other rooms | yes | passed |  |
| Five users posting at the same time all see every message within 10 s | yes | passed |  |
| GET /api/rooms/<room>/messages returns recent messages | yes | passed |  |
| Messages over 1000 characters are rejected | no | passed |  |
| The chat UI loads in a browser without errors | no | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.00 | fixed monthly prices; 0.04 GB out of the Hobby workspace's 5 GB; free instances awake 10 h of 750 free hours |
| Busy | $7.13 | fixed monthly prices; 52.6 GB out of the Hobby workspace's 5 GB, 47.6 GB billed (with a payment method on file; without one Render suspends the services instead); free instances awake 730 h of 750 free hours |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| service | adb-p9gs9-realtime-web | free | $0.00 | free x 1 instance(s) |
| postgres | adb-p9gs9-realtime-db | free | $0.00 | Postgres free |

Teardown: 2 deleted

## Agent's deploy summary

> The app is live at **https://adb-p9gs9-realtime-web.onrender.com**, and every requirement in `TASK.md` passed when I tested it through that URL. It costs $0 a month and needed no human steps.
>
> **What's deployed (both on Render's free plan, Oregon region):**
> - **Web service** `adb-p9gs9-realtime-web` (`srv-db7bvmg473hc73cq8tb0`), a native Node service. WebSocket clients connect to `wss://adb-p9gs9-realtime-web.onrender.com/ws`.
> - **Postgres database** `adb-p9gs9-realtime-db` (`dpg-db7bv8qj9qps73bru9mg-a`), so message history survives restarts. Its connection strings are saved in `.env`, which is git-ignored.
>
> **Tested through the public URL:**
> - The page at `/?room=...` loads.
> - Posting a message returns `201`; an empty message or one over 1000 characters returns `400`.
> - The history endpoint returns the latest messages, oldest first.
> - Two WebSocket clients sent 20 messages at the same time, and both received all 20 in under 0.4 seconds.
> - A client in a different room received none of those messages.
> - An invalid WebSocket message got an error reply.
> - The Server-Sent Events stream delivered a posted message.
>
> **How the code got there:** there were no GitHub credentials, so I couldn't push a repository for Render to build from. Instead, the service builds from Render's public example repo (`render-examples/express-hello-world`). Its build step replaces that repo's contents with this app, which I uploaded to Render as a packed "secret file" called `app.b64`. Everything stays on Render, but redeploying is manual: repack the code, update that file through the Render API, and start a deploy. If a connected Git repo becomes available later, `render.yaml` describes the same setup.
>
> **Free-tier limits:**
> - The web service sleeps after about 15 minutes with no traffic. The first request after that takes about a minute, and open connections drop; the page reconnects on its own.
> - Render's free Postgres expires 30 days after creation unless it is upgraded.
> - The service must stay at one instance, because messages are passed between users inside a single server process.
>
> `deployment.json` is written. I added it and `.env` to `.gitignore`, and committed the app locally.

## Shell commands during deploy

- `5s` `env | cut -d= -f1 | grep -iE 'render|git|gh_|token' ; git remote -v; git log --oneline | head; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/owners | head -c 600; echo; `
- `15s` `gh auth status 2>&1 | head -3; ls ~/.config/gh 2>&1; git config --global --list 2>&1 | head`
- `26s` `printf '.env\ndeployment.json\n' >> .gitignore && git add -A && git commit -qm "Chat rooms app`
- `32s` `git archive --format=tar.gz HEAD package.json package-lock.json server.js store.js public | base64 -w0 > /tmp/app.b64 && wc -c /tmp/app.b64`
- `1m 21s` `python3 - <<'EOF'`
- `1m 26s` `for i in $(seq 1 40); do s=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-db7bvmg473hc73cq8tb0/deploys/dep-db7bvmo473hc73cq8udg | python3 -c 'import json,s`
- `2m 06s` `U=https://adb-p9gs9-realtime-web.onrender.com`
- `2m 16s` `NODE_PATH=$PWD/node_modules node /tmp/remote.js`
- `2m 27s` `cat > deployment.json <<'EOF'`
