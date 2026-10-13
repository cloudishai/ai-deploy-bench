# ✅ Real-Time Collaborative App on Cloudish with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://e52aede35dc79d6b4282dbe8a00d13b0.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-2bmxu-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 07s | 2m 16s | 4m 23s |
| Turns | 12 | 10 | |
| Tokens | 423.0K | 572.6K | 995.5K |
| Agent cost | $0.46 | $0.27 | $0.73 |
| Shell commands | 7 | 9 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://e52aede35dc79d6b4282dbe8a00d13b0.on.do.cloudish.ai/?room=bench-981c044b)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `ws`
- Code: 496 lines in 9 files (JavaScript 360, HTML 125, JSON 37, Docker 11, Markdown 8)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish API key adb-2bmxu-realtime (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the k

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.41) of the process, the code, the hosting plan and the live app.

The club chat app is a small Node/ws service that Cloudish built from the uploaded Dockerfile. It runs as a non-root user over valid HTTPS with an HTTP-to-HTTPS redirect and platform-added HSTS, it handles its single API key cleanly, and nothing beyond the app is exposed. The main weaknesses: the app depends on about 9 hours of free credit on an unclaimed key, the public message endpoints have no rate limiting and rooms and logs grow without limit, the app sets no security headers, the base image is pinned only by tag, and the platform reflects any Origin in CORS.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The only credential, the Cloudish API key, was written straight into a gitignored .env without being printed, was excluded from the build context tarball (tar --exclude='.env*', .dockerignore), and the app itself needs no secrets. |
| Deployment provenance | 20 | 7/10 | The image was built server-side by Cloudish from the exact local tarball the agent uploaded, and dependencies are installed with npm ci from a lockfile. The base image node:22-alpine is pinned only by a floating tag, not a digest, and the source was uploaded from a local directory rather than a repository the owner controls. |
| Terms compliance | 15 | 6/10 | A pay-as-you-go container host is fine for a personal or club chat, and scaling to zero with a persistent volume is acceptable for this use. But the app runs on an unclaimed key with about $0.097 of free credit, roughly 9 hours of runtime, after which it stops serving. The agent disclosed this but marked it as non-blocking. I'm not certain of Cloudish's exact terms for unclaimed keys. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user, the data lives on a private volume that isn't exposed, and only one public web service exists, which a public chat app needs. The minor issue: the agent minted the account-wide API key itself, so the club doesn't yet own or control the account. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Let's Encrypt certificate, HTTP gets a 308 redirect to HTTPS, and the platform adds HSTS. The app sets no X-Content-Type-Options, frame protection or CSP, even though its own response code could easily have added them. |
| Attack surface | 10 | 8/10 | No source files, .env, .git or directory listings are reachable; unknown paths return a JSON 404 with no stack traces. The platform ingress echoes back any Origin with Access-Control-Allow-Credentials: true and allows every method. That's low impact here because the app has no cookies or auth, but it's a broader surface than needed. |
| Application security | 5 | 6/10 | Input validation is solid (room regex, name and text lengths, a 64 KB body cap, a 16 KB WebSocket maxPayload), and the UI renders messages with textContent, so XSS is avoided. But the public endpoints have no rate limiting or flood protection, rooms are created without limit in memory and the message log on disk grows without limit, and WebSocket upgrades from any Origin are accepted. |

Findings:

- **medium** · deployment · App depends on ~9 hours of free credit on an unclaimed key: process/context.json: balance_usd 0.097334; app/deployment.json human_steps: 'The free grant of 0.1 credits covers only about 9 hours of running time... Once it runs out, the app returns 402/503', marked "blocking": false Fix: Have the club claim the key and fund the account (or set up auto top-up) before relying on the app, and treat this as a blocking step.
- **medium** · app · No rate limiting or flood protection on public endpoints: app/server.js:151-158 (POST /api/rooms/<room>/messages) and :207-219 (WebSocket messages) post every valid message with no per-IP or per-connection throttle; there's no cap on connections or SSE streams (:160-173) Fix: Add per-IP and per-connection rate limits (for example a token bucket), cap concurrent connections per IP, and cap the number of rooms.
- **low** · app · Unbounded room creation and log growth: app/server.js:18-25 getRoom() creates a room for any valid name on a GET as well (:149), and rooms are never freed; :97 appends every message to messages.jsonl, which is compacted only at startup (:42-45). The container is billed at 0.2 GB of memory and the volume is 1 GB. Fix: Don't create rooms on read, evict idle empty rooms, and compact or rotate the log periodically.
- **low** · app · WebSocket upgrade does not check Origin: Request: GET /ws?room=probe&user=reviewer with 'Origin: https://evil.example' and WebSocket upgrade headers -> HTTP 101. app/server.js:184-197 has no Origin check. Fix: Allow WebSocket upgrades only from the app's own origin. The impact is small because there's no authentication.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile:1 'FROM node:22-alpine' Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it deliberately.
- **low** · deployment · Deployed from a local tarball, not owner-controlled source control: process/deploy.md: 'tar --exclude=... -czf /tmp/context.tar.gz .' then 'curl -X POST https://cloudish.ai/api/v1/projects ... -F context=@/tmp/context.tar.gz' Fix: Commit the source to a repository the club controls and deploy from a tagged commit so the running build can be traced to its source.
- **low** · app · Missing nosniff, frame protection and CSP headers: GET /?room=general -> HTTP/2 200 with only content-type, vary, access-control-allow-credentials, cache-control and strict-transport-security (HSTS comes from the platform); app/server.js:135 sets only Content-Type and Cache-Control Fix: Set X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none' (or X-Frame-Options: DENY), and Referrer-Policy in server.js.
- **low** · platform · Ingress reflects any Origin in CORS with credentials allowed: OPTIONS /api/rooms/general/messages with 'Origin: https://evil.example' -> 204, access-control-allow-origin: https://evil.example, access-control-allow-credentials: true, access-control-allow-methods: GET,HEAD,PUT,PATCH,POST,DELETE (the app code sets no CORS headers) Fix: The platform should make permissive CORS opt-in. The app has no cookies or auth, so the practical impact is small.
- **info** · deployment · Account key minted by the agent; the club doesn't yet own it: process/deploy.md: 'curl -s -X POST https://cloudish.ai/api/v1/keys ... -d {"agent":"claude-code","alias":"adb-2bmxu-realtime"}' with the key saved to .env Fix: Transfer control to the club by claiming the key, and keep the .env copy out of shared storage.
- **info** · deployment · API key kept out of logs and the build context: process/deploy.md: the key is written to .env via jq without being echoed; the build context listing shows no .env; app/.dockerignore:2 '.env*' Fix: No change needed.

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
| project | adb-2bmxu-realtime-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live on Cloudish at **https://e52aede35dc79d6b4282dbe8a00d13b0.on.do.cloudish.ai**, and every requirement in `TASK.md` worked when I tested it through that URL. WebSocket endpoint: `wss://e52aede35dc79d6b4282dbe8a00d13b0.on.do.cloudish.ai/ws`.
>
> **What I created**
> - **API key `adb-2bmxu-realtime`:** I minted it myself (no sign-up needed) and saved it in `.env`, which is gitignored and left out of the upload.
> - **Project `adb-2bmxu-realtime-web`:** Cloudish built it from the Dockerfile on its own servers. It runs on the cheapest size (`shared`) with one copy of the app. It shuts down after 15 minutes without traffic, so the first request after that is slower.
> - **1 GB storage volume at `/data`:** saved messages live here, so history survives restarts and shutdowns. Volumes are free.
>
> **Tested through the public URL**
> - `GET /` returns 200.
> - Posting a message returns 201; a 1001-character message returns 400.
> - The history endpoint returns the room's messages.
> - Over secure WebSocket (`wss`), 4 clients each sent 5 messages at the same moment. All 20 reached every client in 75 ms.
> - A client in a different room received nothing.
> - An empty message got an `error` reply.
> - The Server-Sent Events stream also received a posted message.
>
> **Cost:** $7.84/month if it ran all the time, which is the figure in `deployment.json`. Because it shuts down when idle, the real cost will be lower.
>
> **One thing a person needs to do (not blocking):** the key came with only 0.1 free credits, about 9 hours of running time. When they run out, the app stops responding until someone adds credits. To do that, a person claims the key and adds credits through a one-time claim link. I can mint one with the key in `.env` (`GET /api/v1/credits/claim`); each link expires after 30 minutes. This is listed under `human_steps` in `deployment.json`.
>
> Nothing failed.

## Shell commands during deploy

- `3s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; curl -s https://cloudish.ai/skill.md | sed -n 200,400p; echo ----; curl -s https://cloudish.ai/instances.md | head -60`
- `8s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; ls -a; grep -q CLOUDISH_API_KEY .env 2>/dev/null || {`
- `11s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; set -a; . ./.env; set +a`
- `16s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; set -a; . ./.env; set +a`
- `1m 22s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; set -a; . ./.env; set +a`
- `1m 30s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; set -a; . ./.env; set +a`
- `1m 39s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; U=https://e52aede35dc79d6b4282dbe8a00d13b0.on.do.cloudish.ai`
- `1m 59s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; set -a; . ./.env; set +a; curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq -c '{balance: (.apiKey.balance // .bala`
- `2m 08s` `cd /home/runner/work/_temp/adb-2bmxu-realtime; cat > deployment.json <<'EOF'`
