# ✅ Real-Time Collaborative App on Cloudish with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-y1ogp-realtime.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $0.41)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-y1ogp-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 56s | 2m 36s | 4m 32s |
| Turns | 10 | 11 | |
| Tokens | 356.0K | 621.7K | 977.7K |
| Agent cost | $0.41 | $0.32 | $0.73 |
| Shell commands | 6 | 9 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-y1ogp-realtime.on.do.cloudish.ai/?room=bench-a236f076)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `ws`
- Code: 428 lines in 9 files (JavaScript 281, HTML 136, JSON 30, Markdown 15, Docker 11)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-y1ogp-realtime' (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the key

## Security and compliance review

**85/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.35) of the process, the code, the hosting plan and the live app.

The chat app was built and deployed cleanly: the Cloudish key never left a chmod-600 .env, the image was built from the agent's own source with a lockfile and runs as non-root, and the site is HTTPS-only with nothing extra exposed. The main weaknesses are hosting on an unclaimed key with about 9 hours of free credit, so the club's app goes down unless someone claims and funds it, and public endpoints with no rate limits, Origin check or storage caps. The app also sets no security headers and the base image isn't pinned by digest.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The only credential, the Cloudish API key, was written straight to a chmod-600 .env without being printed (jq 'del(.key, .claimUrl)'), excluded from the build context and .dockerignore, and never sent to the container. The app itself needs no secrets. |
| Deployment provenance | 20 | 8/10 | The image was built server-side from a tarball of the agent's own working directory, which it listed before upload, and dependencies were installed with npm ci from a lockfile. The base image node:24-slim is a floating tag with no digest pin. |
| Terms compliance | 15 | 6/10 | A pay-as-you-go container platform suits a personal club app. But the deployment runs on an unclaimed key with only 0.1 free credits (about 9.3 running hours), so the app stops serving within days unless a human claims the key and adds credits. The agent disclosed this but marked it non-blocking. |
| Least privilege | 15 | 10/10 | The container runs as the non-root node user, and the SQLite volume is attached privately to the single app. Only the web service is public, which the app needs. |
| Transport security | 10 | 8/10 | The site is HTTPS-only with a valid Let's Encrypt certificate, HTTP gets a 308 redirect, and the platform adds HSTS. The app doesn't set X-Content-Type-Options, frame protection or a CSP, though it easily could. |
| Attack surface | 10 | 9/10 | Probes for source files, .env, .git and admin paths all return the app's JSON 404, and nothing else is exposed. The only extra detail is the platform's default nginx error pages, which reveal the server software. |
| Application security | 5 | 6/10 | Input validation is solid, SQL is parameterized and the UI renders with textContent, so no injection or XSS was found. Public endpoints have no rate limiting and no caps on connections or storage, and the WebSocket accepts any Origin. Anyone can post under any name, flood rooms, fill the volume or keep the app awake to burn credits. |

Findings:

- **medium** · deployment · App runs on an unclaimed key with about 9 hours of free credit: process/deployment.json: plan 'unclaimed key, 0.1 free credits'; the human step says the app 'returns 402/503 until more credits are added' and is marked blocking:false. process/context.json: balance_usd 0.098167. deploy.md key creation: runningHoursLeft 9.3. Fix: Claim the key to a human owner's account and fund it before handing the app over, or mark this step as blocking so the club knows the app goes down otherwise.
- **medium** · app · No rate limiting or resource caps on public write and stream endpoints: app/server.js:130-139 (POST messages), 140-161 (SSE) and 169-202 (WebSocket) apply no per-client limits. Rooms are unbounded and every message is stored permanently (server.js:81), on a 1 GB volume with prepaid, per-second billing. Fix: Add per-IP and per-connection rate limits, cap concurrent connections and rooms, and prune or cap stored history per room.
- **low** · app · WebSocket accepts any Origin, and display names are unauthenticated: An upgrade request to /ws?room=review-probe&user=probe with 'Origin: https://evil.example' returned 101. server.js:170-178 never checks the Origin header, and the user name comes straight from the query string. Fix: Check the Origin header against the app's own host. Optionally add a simple shared room passcode for the club.
- **low** · app · No security headers set by the app: GET /?room=general returned only content-type, cache-control and strict-transport-security (HSTS is added by the platform). There was no X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. Fix: Set X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none' and Referrer-Policy on the HTML and JSON responses in server.js.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile:1 'FROM node:24-slim' Fix: Pin the base image by digest, e.g. node:24-slim@sha256:..., and update it on purpose.
- **info** · platform · Ingress default error pages reveal nginx: GET /api/rooms/%ZZ/messages and TRACE / returned nginx HTML error pages ('<center>nginx</center>'). Fix: Platform: serve generic error pages without the server banner.
- **info** · platform · Platform builder pulls an unpinned helper image: deploy.md build events: 'Pulling image "curlimages/curl:latest"' in the Cloudish build job Fix: Platform: pin builder helper images by digest.

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
| project | adb-y1ogp-realtime-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-y1ogp-realtime.on.do.cloudish.ai**, and every requirement in `TASK.md` passed when I tested it through that URL. One thing to act on: it's running on Cloudish's free credit, which covers only about 9.3 hours of running time.
>
> **What I set up on Cloudish:**
> - **API key:** I created a key named `adb-y1ogp-realtime` myself (no sign-up needed). It's saved in `.env` and was never printed or uploaded.
> - **App:** project `adb-y1ogp-realtime-web`, built by Cloudish from my Dockerfile. It runs one container on the cheapest size (`shared`) and shuts down when idle.
> - **Storage:** a 1 GB persistent volume holds the chat history, so it survives restarts and redeploys.
> - **Address:** I set the memorable subdomain above; it has a valid HTTPS certificate.
> - **Real-time:** `deployment.json` records WebSocket at `wss://adb-y1ogp-realtime.on.do.cloudish.ai/ws`.
>
> **Test results against the public URL:**
> - The web page loads.
> - Two users posted 20 messages at the same time, plus one sent over HTTP. Both received all 21, the slowest in about 140 ms (the limit is 2 seconds).
> - A user in another room received none of them.
> - History returns the right messages, oldest first.
> - Invalid messages are rejected: `400` over HTTP, and an error reply over WebSocket.
> - Server-Sent Events delivered a message, and posting returns `201`.
>
> **Cost:** Cloudish bills per second only while the container is running. At about an hour of use a day that's roughly $0.41/month; kept on all the time it would be about $7.84/month. The first request after an idle period takes a moment while the container starts.
>
> **Your step (listed in `deployment.json`):** claim the key and add credits; once the free credit runs out, the app stops serving until you do. To get a claim link, call `GET https://cloudish.ai/api/v1/credits/claim` with the key from `.env`. The link expires after 30 minutes.

## Shell commands during deploy

- `15s` `curl -sL https://cloudish.ai/skill.md`
- `20s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; printf '.env\n' >> .gitignore; printf '.env*\n' >> .dockerignore`
- `24s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; source .env; mkdir -p /tmp/ctx && tar --exclude='.env*' --exclude='.git' --exclude=node_modules --exclude=data --exclude=deployment.json -czf /tmp/ctx/co`
- `28s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; source .env; for i in $(seq 40); do s=$(curl -s https://cloudish.ai/api/v1/images/builds/245 -H "Authorization: Bearer $CLOUDISH_API_KEY"); st=$(echo "$s`
- `1m 14s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; source .env; curl -s https://cloudish.ai/api/v1/projects/adb-y1ogp-realtime/adb-y1ogp-realtime-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq 'del`
- `1m 19s` ❌ `cd /home/runner/work/_temp/adb-y1ogp-realtime; source .env; curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-y1ogp-realtime/adb-y1ogp-realtime-web/subdomain -H "Authorization: Bearer $CLOUDISH_A`
- `1m 28s` `U=https://adb-y1ogp-realtime.on.do.cloudish.ai; for i in $(seq 24); do c=$(curl -s -o /dev/null -w '%{http_code}' $U/health); [ "$c" = 200 ] && break; sleep 10; done; echo $c; curl -sv $U/health 2>&1 `
- `2m 05s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; cat > /tmp/ctx/e2e.mjs <<'EOF'`
- `2m 28s` `cd /home/runner/work/_temp/adb-y1ogp-realtime; cat > deployment.json <<'EOF'`
