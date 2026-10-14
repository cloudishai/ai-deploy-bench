# ✅ Real-Time Collaborative App on Cloudish with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://c4b2e87f16b9f8eb5957749a194992eb.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-25uju-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 17s | 2m 53s | 5m 09s |
| Turns | 11 | 10 | |
| Tokens | 401.5K | 567.8K | 969.3K |
| Agent cost | $0.43 | $0.30 | $0.73 |
| Shell commands | 7 | 8 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://c4b2e87f16b9f8eb5957749a194992eb.on.do.cloudish.ai/?room=bench-d9930a4b)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Data: Files on a persistent volume
- Libraries: ws
- Packaging: Docker (node:22-alpine)
- Hosting: Cloudish container (shared) with a persistent volume
- Code: 458 lines in 9 files (JavaScript 312, HTML 135, JSON 27, Markdown 14, Docker 11)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key adb-25uju-realtime (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the key i

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.33) of the process, the code, the hosting plan and the live app.

The chat app is cleanly built and deployed: the Cloudish API key never left the local .env, the image is built from the uploaded source with a locked dependency tree and runs as non-root, it's served only over HTTPS with HSTS, and nothing beyond the app is exposed. The main weakness is that it runs on an unclaimed 0.1-credit grant that keeps it up for only about 9 hours unless the owner adds credits. Smaller issues are the unpinned base image, missing browser security headers, no rate limiting or Origin check, and test messages left in production.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to a local .env without being printed (jq 'del(.key,.claimUrl)'), kept out of the upload tarball and .dockerignore, and never appears in source, logs or the deployed image. The app itself needs no secrets. |
| Deployment provenance | 20 | 7/10 | The running image registry.do.cloudish.ai/builds/103:4b2b0345ca8f was built by the platform from a source tarball the agent uploaded, and dependencies are locked through package-lock.json with npm ci. The base image node:22-alpine is a floating tag with no digest pin. |
| Terms compliance | 15 | 5/10 | Personal use fits Cloudish's pay-as-you-go model as far as I know (I'm not certain of the exact terms). However, the app runs on an unclaimed key with a 0.1-credit grant, about 9 hours of runtime, after which it returns 402/503. A club chat has to stay up, and that depends on a human step listed as non-blocking. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user, the /data volume is only mounted into the app, and the only public resource is the web service, which has to be public. The project access is 'open', which is required for a public chat. |
| Transport security | 10 | 8/10 | Served over HTTPS with a valid Let's Encrypt certificate. HTTP returns a 308 redirect to HTTPS and the platform adds HSTS. The app sets no X-Content-Type-Options, frame-ancestors/X-Frame-Options or CSP, though it could have. |
| Attack surface | 10 | 9/10 | Probes for /.env, /.git/config, /server.js, /package.json, /Dockerfile and /data/ all return a JSON 404, and errors return generic JSON with no stack traces. The only extra endpoint is a benign /health. End-to-end test messages were left in the production history. |
| Application security | 5 | 7/10 | Input is validated well (room regex, 1-1000 character text, 64 KB body and WebSocket payload caps), and the UI renders with textContent, so stored XSS is prevented. Nothing limits request rates, room creation or concurrent SSE/WebSocket connections, and the WebSocket accepts any Origin. |

Findings:

- **medium** · deployment · App runs on an unclaimed free credit grant that lasts about 9 hours: process/deployment.json human_steps: 'The free grant is 0.1 credits, about 9 hours of running time ... After that the app returns 402/503 until credits are added', marked blocking:false; process/context.json balance_usd 0.097336 Fix: Have the owner claim the key and add credits (or set up billing) before handing the app over, and treat this as a blocking step for an app that must stay up.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile line 1: FROM node:22-alpine Fix: Pin the base image to a specific digest (node:22-alpine@sha256:...) and update it on purpose.
- **low** · app · No rate limiting or caps on rooms and connections: app/server.js lines 146-182 and 192-232: any valid room name creates a .jsonl file and an in-memory entry, and nothing limits POST rate or the number of SSE/WebSocket clients Fix: Add per-IP rate limits for posts and connections, cap the number of rooms and concurrent streams, and evict idle rooms from memory.
- **low** · app · WebSocket upgrade does not check Origin: Upgrade request to /ws?room=reviewtest&user=reviewer with Origin: https://evil.example -> 101 Switching Protocols; app/server.js lines 192-200 check only the path, room and user Fix: Allow only the app's own origin on WebSocket upgrades so other sites can't post on visitors' behalf.
- **low** · app · Missing browser security headers: GET / response headers: only content-type, cache-control and strict-transport-security (HSTS from the platform); no X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy Fix: Set X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none' (or X-Frame-Options: DENY), and Referrer-Policy in server.js responses.
- **info** · platform · Platform build job pulls a floating helper image: process/deploy.md build events: Pulling image "curlimages/curl:latest" Fix: The platform should pin the images its build pipeline uses.
- **info** · deployment · End-to-end test data left in production history: GET /api/rooms/e2e1791991222506/messages -> 200 with test messages from users bob/alice/dan, posted by the agent's checks in process/deploy.md Fix: Use a throwaway room that is cleaned up afterwards, or clear test data from the volume after verifying.
- **info** · app · Display names are unauthenticated: app/server.js lines 160-162 and 195: user comes from the request body or query string without verification Fix: This is acceptable under the spec for a hobby club. If impersonation becomes a problem, add a lightweight room passcode or sessions.

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
| project | adb-25uju-realtime-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live on Cloudish at **https://c4b2e87f16b9f8eb5957749a194992eb.on.do.cloudish.ai**, with WebSockets at `wss://c4b2e87f16b9f8eb5957749a194992eb.on.do.cloudish.ai/ws`. Every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What I created:**
> - **API key `adb-25uju-realtime`:** created through Cloudish's open API. It is saved in `.env`, which is excluded from git and from the uploaded build.
> - **Container app `adb-25uju-realtime-web`:** built on Cloudish's servers from the `Dockerfile`, running on the cheapest size (`shared`) as a single instance. It shuts down after 15 minutes without requests and starts again on the next one.
> - **1 GB volume at `/data`:** stores chat history so it survives restarts and redeploys. Volumes are free.
>
> **Tested through the public URL:**
> - The chat page loads.
> - Two users sent 20 messages at the same time over WebSocket. Both received all 21 messages (including one sent over HTTP) in the same order, all within 100 ms.
> - A user in another room received nothing.
> - An empty message over WebSocket got an `error` reply.
> - Over HTTP, a valid message returned `201`, and empty or 1001-character messages returned `400`.
> - The history API returned the room's messages oldest first.
> - A Server-Sent Events client received a new message live.
>
> **Limitations:**
> - **Credits will run out:** the key came with only 0.1 free credits, about 9 hours of running time. After that the app returns 402 or 503 until someone adds credits. I listed claiming the key and adding credits under `human_steps`; it doesn't block anything now.
> - **Cost:** the estimate is $7.84/month only if the app runs nonstop. In practice it is billed per second of use.
> - **Cold start:** after an idle shutdown, the first request takes a few seconds while the app starts.
> - **One instance only:** live delivery happens inside one process and the volume attaches to one container, so the app can't run as more than one copy.
>
> I didn't test that history survives a restart on Cloudish. The app is set up so it should.

## Shell commands during deploy

- `20s` `curl -sL https://cloudish.ai/skill.md`
- `28s` `cd /home/runner/work/_temp/adb-25uju-realtime; grep -q CLOUDISH_API_KEY .env 2>/dev/null || { r=$(curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"agent":"clau`
- `36s` `cd /home/runner/work/_temp/adb-25uju-realtime; set -a; . ./.env; set +a`
- `41s` `cd /home/runner/work/_temp/adb-25uju-realtime; . ./.env`
- `1m 53s` `cd /home/runner/work/_temp/adb-25uju-realtime; . ./.env; sleep 5; curl -s https://cloudish.ai/api/v1/projects/$CLOUDISH_ALIAS/adb-25uju-realtime-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq '`
- `2m 01s` `U=https://c4b2e87f16b9f8eb5957749a194992eb.on.do.cloudish.ai; for i in $(seq 1 20); do c=$(curl -s -o /dev/null -w "%{http_code}" -m 30 $U/health); echo $c; [ "$c" = 200 ] && break; sleep 6; done`
- `2m 27s` `mkdir -p /tmp/e2e; cat > /tmp/e2e/e2e.cjs <<'EOF'`
- `2m 44s` `cd /home/runner/work/_temp/adb-25uju-realtime; cat > deployment.json <<'EOF'`
