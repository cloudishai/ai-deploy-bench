# ✅ Real-Time Collaborative App on Cloudish with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-nthw4-realtime-web.cloudish.app (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $0.41)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-nthw4-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 00s | 1m 42s | 3m 42s |
| Turns | 10 | 10 | |
| Tokens | 370.1K | 582.0K | 952.1K |
| Agent cost | $0.43 | $0.32 | $0.75 |
| Shell commands | 8 | 8 | |

App answered 0s after the agent finished deploying.

**Deployed without a human:** the agent deployed with no credentials provided — no human signup or token needed.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-nthw4-realtime-web.cloudish.app/?room=bench-055d2108)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Data: SQLite (on a persistent volume)
- Libraries: ws
- Packaging: Docker (node:22-slim)
- Hosting: Cloudish container (shared) with a persistent volume
- Code: 475 lines in 10 files (JavaScript 344, HTML 121, Markdown 31, JSON 29, Docker 10)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Node.js with ws and built-in SQLite on a Cloudish volume is a minimal, well-reasoned stack for a single-instance realtime chat, and the build matches what STACK.md recorded.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | WebSockets via `ws` with in-process per-room fan-out, plus SQLite history on a persistent volume, match the realtime and durability requirements well. The UI is served from the same process. |
| Proportion | 30 | 9/10 | One process and one npm dependency, with built-in node:sqlite and plain HTML/JS. The optional SSE fallback reuses the same broadcast core and adds little code. |
| Platform fit | 30 | 9/10 | This is exactly Cloudish's model: a single long-running container built server-side, with a /data volume and sleep-on-idle that suits a low-traffic club app. The single instance the volume imposes matches the in-memory broadcast design, as STACK.md argues. |

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-nthw4-realtime' (mint a fresh link with GET https://cloudish.ai/api/v1/credits/claim using t

## Security and compliance review

**76/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.42) of the process, the code, the hosting plan and the live app.

A small, carefully built Node.js chat app. The Cloudish key never appeared in logs or the build context, input validation and output encoding are solid, nothing beyond the app is exposed, and the site is served over HTTPS with HSTS and a redirect from HTTP. The main weaknesses are in operations: the app runs on an unclaimed key with a free grant of about 9 awake hours, the container runs as root, the base image isn't pinned by digest, and the public endpoints have no rate limits, Origin check or app-set security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The Cloudish API key was written straight to a chmod-600 .env without ever being printed, sourced into the shell only when needed, and left out of the uploaded build context. The app itself needs no secrets. The only gap is that .dockerignore doesn't list .env, so the exclusion relies on the tar command alone. |
| Deployment provenance | 20 | 7/10 | Cloudish built the running image (builds/207:c660a0fd659e) from the uploaded source tarball, and dependencies install reproducibly with npm ci from a lockfile with a single dependency. However, the base image node:22-slim is a floating tag with no digest, the source exists only as a local tarball with no repository, and the account key is still unclaimed, so the owner doesn't yet control the account. |
| Terms compliance | 15 | 6/10 | Personal use on prepaid Cloudish credits seems consistent with the provider's terms (I'm not certain of Cloudish's exact terms), and sleeping after 15 idle minutes is acceptable for a club chat. But the app runs on an unclaimed key with only the 0.1-credit free grant, about 9 awake hours, and it will start returning 402/503 unless a human claims the key and adds credits. |
| Least privilege | 15 | 7/10 | There is a single replica with a private volume mounted only at /data and no extra public services, and open access is needed for a public chat. The container runs as root, though, because the Dockerfile has no USER line. |
| Transport security | 10 | 8/10 | The certificate is a valid Let's Encrypt wildcard over TLS 1.3, HTTP returns a 308 redirect to HTTPS, and the platform adds HSTS. The app sets no X-Content-Type-Options, frame protection or CSP, even though it controls its own response headers. |
| Attack surface | 10 | 9/10 | Source files, .env, .git and admin paths all return the app's JSON 404, there are no directory listings or stack traces, and the only extra endpoint is a harmless /healthz. A malformed URL gets the platform's nginx 400 page, which reveals the server software. |
| Application security | 5 | 7/10 | Input validation is solid: length limits, rejection of control characters, a 64 KB body cap, a 16 KB WebSocket payload cap and parameterized SQL. The UI renders with textContent, so it is XSS-safe. There is no rate limiting and no cap on WebSocket or SSE connections, and the WebSocket upgrade accepts any Origin. |

Findings:

- **medium** · deployment · App depends on an unclaimed key with a 0.1-credit free grant: process/deployment.json human_steps: 'The key only has the 0.1-credit free grant (~9 hours of awake time). When it runs out the app answers 402/503'; /api/v1/me returned {'balance': 0.099362, 'creditsPerHour': 0.010733} Fix: Have the owner claim the key and fund it, or set up auto top-up, before relying on the app. Record the owner's account in the handoff.
- **low** · deployment · Container runs as root: app/Dockerfile has no USER directive (FROM node:22-slim ... CMD ["node", ...]) Fix: Add `USER node` (after chown of /data or relying on the volume's permissions) so the process runs unprivileged.
- **low** · deployment · Base image not pinned by digest; source only uploaded as a local tarball: app/Dockerfile line 1: FROM node:22-slim; process/deploy.md: tar ... -czf /tmp/context.tar.gz . && curl -X POST https://cloudish.ai/api/v1/projects ... -F context=@/tmp/context.tar.gz Fix: Pin node:22-slim@sha256:<digest> and keep the source in a repository the owner controls, deploying from a tagged commit.
- **low** · app · No rate limiting or connection caps on public endpoints: app/server.js lines 140-163 and 179-225: POST /api/rooms/<room>/messages, SSE /events and /ws accept unlimited requests and connections per client; open WebSocket connections also keep the paid container awake Fix: Add per-IP rate limits on message posts and caps on concurrent WebSocket and SSE connections per IP.
- **low** · app · WebSocket upgrade does not check Origin: Upgrade request to wss://adb-nthw4-realtime-web.cloudish.app/ws?room=review-probe&user=rev with Origin: https://evil.example returned HTTP/1.1 101 Switching Protocols (server.js lines 179-191 do not check req.headers.origin) Fix: Reject upgrades whose Origin is not the app's own host. The impact is low because the app has no cookies or auth.
- **low** · app · Missing X-Content-Type-Options, frame protection and CSP: GET https://adb-nthw4-realtime-web.cloudish.app/ response headers: content-type, cache-control, strict-transport-security only Fix: Set X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none' (or X-Frame-Options: DENY) and Referrer-Policy in sendJson and the index handler.
- **info** · deployment · .dockerignore does not exclude .env: app/.dockerignore lists only node_modules, data, .git, test; .env was kept out of the build context only by tar --exclude='.env*' in process/deploy.md Fix: Add .env* to .dockerignore as defense in depth for future redeploys.
- **info** · platform · Platform nginx error page reveals server software: GET /api/rooms/%E0%A4%A/messages returned a 400 HTML page '<center>nginx</center>' from the ingress Fix: Nothing the agent can do; the platform could serve a generic error page.

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
| Light use | $0.11 | containers awake 10 h at their size's hourly rate; no bandwidth charges |
| Busy | $7.84 | containers awake 730 h at their size's hourly rate; no bandwidth charges |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-nthw4-realtime-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-nthw4-realtime-web.cloudish.app**, and every requirement in `TASK.md` passed when I tested it through that URL. The WebSocket address is `wss://adb-nthw4-realtime-web.cloudish.app/ws`.
>
> **What I deployed:**
> - **Cloudish key `adb-nthw4-realtime`:** I created it myself with no signup. It's saved in `.env`, which is not committed or deployed.
> - **App `adb-nthw4-realtime-web`:** Cloudish built it from the Dockerfile. It runs on the cheapest size (`shared`) and goes to sleep after 15 idle minutes. It costs $0.0107 per hour while awake, so about $0.41 a month at an hour a day, or $7.84 if it ran around the clock.
> - **Storage:** a 1 GB persistent volume at `/data` keeps the message history across restarts and redeploys. Volumes aren't billed.
>
> **Results through the public URL:**
> - `GET /` returned 200.
> - 4 WebSocket users each sent 5 messages at the same time, and every user got all 20 within about 115 ms. Users in a different room got none of them.
> - Empty and 1001-character messages got an error reply over WebSocket and a 400 over HTTP.
> - Sending over HTTP returned 201, and the message also reached the WebSocket users.
> - History returned 200 with messages oldest first, and the Server-Sent Events stream also worked.
>
> **What to know:**
> - **Credits will run out soon:** the key only has the free 0.1 credits, which is about 9 hours of awake time. After that the app stops answering until someone claims the key and adds credits. I listed this in `human_steps` as non-blocking, since nothing needed a person to deploy.
> - **Slow first load after sleep:** the first request after the app has been asleep takes a few seconds, and my first one got a 503 while it started. The web page reconnects automatically.
> - **Open connections keep it awake:** an open WebSocket connection counts as activity, so the app stays awake and billed while anyone is connected.
>
> All of this, including how to redeploy, is in `deployment.json`.

## Shell commands during deploy

- `12s` `curl -s https://cloudish.ai/skill.md`
- `16s` `curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"alias":"adb-nthw4-realtime","agent":"claude-code","model":"claude-opus-5-5"}' > /tmp/key.json && python3 -c "`
- `19s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude=node_modules --exclude=data --exclude=deployment.json -czf /tmp/context.tar.gz . && tar tzf /tmp/context.tar.gz && curl`
- `23s` `set -a && . ./.env && set +a && for i in $(seq 1 40); do s=$(curl -s https://cloudish.ai/api/v1/images/builds/594 -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c "import json,sys;b=json.load`
- `46s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/projects/$CLOUDISH_ALIAS/adb-nthw4-realtime-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c "import json,sys;d=json.loa`
- `50s` `set -a && . ./.env && set +a && curl -s -X PUT https://cloudish.ai/api/v1/projects/$CLOUDISH_ALIAS/adb-nthw4-realtime-web/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: appli`
- `1m 18s` `cat > /tmp/remote.mjs <<'EOF'`
- `1m 35s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/docker/$CLOUDISH_ALIAS/adb-nthw4-realtime-web/logs -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c "import json,sys;print(j`
