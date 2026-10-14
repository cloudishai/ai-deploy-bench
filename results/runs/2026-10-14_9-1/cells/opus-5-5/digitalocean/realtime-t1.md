# ✅ Real-Time Collaborative App on DigitalOcean with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-pzps1-realtime-nd5yo.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-pzps1-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 36s | 1m 30s | 3m 05s |
| Turns | 10 | 8 | |
| Tokens | 345.6K | 369.4K | 715.0K |
| Agent cost | $0.37 | $0.18 | $0.56 |
| Shell commands | 7 | 7 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-pzps1-realtime-nd5yo.ondigitalocean.app/?room=bench-ebed2ad2)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `ws`
- Code: 405 lines in 10 files (JavaScript 279, HTML 115, JSON 25, Markdown 17, YAML 16, Docker 11)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**86/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.33) of the process, the code, the hosting plan and the live app.

The chat app is deployed cleanly on a paid, always-on App Platform Basic instance that fits a personal club. It needs no secrets, runs as a non-root user, enforces HTTPS and exposes nothing beyond the app. The main weaknesses are provenance and abuse resistance. The image was built locally from code with no repository, using a base image and deploy tag that aren't pinned to a digest. The app has no rate limiting, never frees rooms it creates on demand, doesn't check the WebSocket Origin and sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets and none appear in source, the image or the logs. The DigitalOcean token was only used through an environment variable. The one minor point is that `doctl registry login` left a Docker registry credential valid for 30 days on the build host. |
| Deployment provenance | 20 | 6/10 | The image was built on the agent's machine and pushed straight to the owner's private registry, with no source repository or CI behind it. The base image `node:22-alpine` and the tag `v1` can both change and are not pinned by digest. The `ws` dependency uses a caret range, and doctl was downloaded without a checksum check. |
| Terms compliance | 15 | 10/10 | This is a personal or club app on a paid App Platform Basic instance ($5/month), which stays up and doesn't sleep. The free DOCR Starter tier allows this use. Running a single instance with in-memory history fits a small hobby club. |
| Least privilege | 15 | 10/10 | The container runs as the non-root `node` user, there is no data store to expose, the registry is private, and only the one HTTP service is public. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. WebSockets use wss://. The app sets none of HSTS, X-Content-Type-Options, frame protection or CSP, though it could have. |
| Attack surface | 10 | 10/10 | Requests for .env, .git, package.json, source files and the app spec all return a generic JSON 404. Errors don't leak stack traces, and the only extra endpoint is a harmless /healthz. |
| Application security | 5 | 6/10 | Input checks are solid: text length, room and user checks, a 16 KB body limit and a 64 KB WebSocket payload limit. The client renders with textContent, so there is no XSS. But public endpoints have no rate limiting, any request can create a room in memory that is never freed, and there are no limits on connections or SSE streams. Together these leave the app open to easy resource-exhaustion abuse. |

Findings:

- **medium** · deployment · Image built locally and pushed with no source of record: process/deploy.md: `docker build ... -t registry.digitalocean.com/adb-pzps1-realtime/adb-pzps1-realtime-web:v1 . && docker push ...`, then `doctl apps create --spec .do/app.yaml`. build.md shows `git status` -> 'fatal: not a git repository'. Fix: Keep the code in a repository the owner controls and build from it, either with App Platform's git/Dockerfile source or with CI. Deploy by image digest so the running image can be traced back to a commit.
- **medium** · deployment · Base image and deployed tag can change: app/Dockerfile:1 `FROM node:22-alpine`. app/.do/app.yaml has `tag: v1`, not a digest. Fix: Pin the base image as `node:22-alpine@sha256:...`. Deploy an immutable digest, or a unique tag per build, instead of a reusable tag.
- **medium** · app · Unbounded room creation and no abuse limits: app/server.js:16-23: `getRoom` adds any valid room name to a global Map that is never pruned. It is called on every GET /api/rooms/<room>/messages (line 114), every SSE subscription (139) and every WebSocket connection (175). There is no rate limiting on POST /messages (117-129) or WebSocket messages (181-193), and no cap on connections or SSE streams. Fix: Rate-limit posts and connections per IP. Don't create a room on a read-only GET, and evict rooms that are empty or idle. Cap the total number of rooms, connections and streams.
- **low** · deployment · Dependency range and unverified tool download: app/package.json: `"ws": "^8.18.0"`. No package-lock.json is in the snapshot, although `npm ci` in the Dockerfile needs one. deploy.md: `curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/... | tar xz` with no checksum check. Fix: Commit package-lock.json and pin exact versions. Verify release checksums before installing tools.
- **low** · app · WebSocket upgrade does not check Origin: app/server.js:163-171 accepts upgrades from any Origin. A request with `Origin: https://evil.example` to /ws?room=review&user=tester got `HTTP/1.1 101 Switching Protocols`. Fix: Accept only the app's own Origin, so other sites can't open sockets from visitors' browsers to post or read messages. The impact is low because the app has no authentication.
- **low** · app · Security headers missing: `GET /?room=general` response headers show no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. server.js:97 sets only Content-Type. Fix: Set HSTS, `X-Content-Type-Options: nosniff`, and a CSP with `frame-ancestors 'none'` in the Node responses.
- **info** · deployment · Long-lived registry login on the build host: process/deploy.md: `doctl registry login` -> 'Login valid for 30 days'. Fix: Pass `--expiry-seconds` for a short-lived login, or run `docker logout` after pushing.
- **info** · app · No sensitive files exposed: GET /.env, /.git/config, /package.json, /server.js, /Dockerfile, /.do/app.yaml and /package-lock.json all return 404 `{"error":"not found"}`. A bad percent-encoding in /api/rooms/%E0/messages returns 400 with no stack trace. Fix: No action needed.
- **info** · platform · HTTPS enforced by the platform: `curl -I http://adb-pzps1-realtime-nd5yo.ondigitalocean.app/` -> 301 to https. The certificate is CN=ondigitalocean.app, issued by Google Trust Services WE1, valid until 2026-12-22. Fix: No action needed.

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
| Light use | $5.00 | fixed monthly prices; 0.0373 GiB out of a 50 GiB allowance |
| Busy | $5.00 | fixed monthly prices; 49 GiB out of a 50 GiB allowance |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| app | adb-pzps1-realtime | adb-pzps1-realtime-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-pzps1-realtime-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-pzps1-realtime | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-pzps1-realtime-nd5yo.ondigitalocean.app**, and everything in `TASK.md` worked when I tested it through that public URL.
>
> **What's deployed:**
> - **Container registry:** a free starter-tier DigitalOcean registry, `adb-pzps1-realtime`, holding the app's Docker image (`adb-pzps1-realtime-web:v1`).
> - **App:** an App Platform app, `adb-pzps1-realtime`, running one service (`adb-pzps1-realtime-web`) on the smallest instance size (`apps-s-1vcpu-0.5gb`) in the NYC region. HTTPS is handled automatically by App Platform.
> - **Cost:** about $5/month, all of it for the app instance.
> - **Real-time URL:** `wss://adb-pzps1-realtime-nd5yo.ondigitalocean.app/ws`, recorded in `deployment.json`.
>
> **Results through the public URL:**
> - **Web page:** `GET /` returns `200`.
> - **Posting over HTTP:** a valid message returns `201`, and a 1001-character message returns `400`.
> - **History:** `GET /api/rooms/<room>/messages` returns the room's messages in the expected shape.
> - **Live delivery:** two users in one room each sent 5 messages at the same time over `wss://`. Both received all 10, plus one sent over HTTP. The slowest arrived in about 0.24 seconds, well under the 2-second limit.
> - **Room isolation:** a user connected to another room received nothing.
> - **Invalid WebSocket message:** an empty message got an error reply.
> - **Server-Sent Events:** the event stream delivered the message sent over HTTP.
>
> No steps needed a person, so `human_steps` is empty.
>
> **Limitation:** message history and the list of who's online are kept in memory. They reset whenever the app restarts or is redeployed, so the service has to stay at one instance. The steps to redeploy are in the notes in `deployment.json`.

## Shell commands during deploy

- `4s` `which doctl; git status 2>&1 | head -2; curl -s -H "Authorization: Bearer $DIGITALOCEAN_ACCESS_TOKEN" https://api.digitalocean.com/v2/registry; echo; curl -s -H "Authorization: Bearer $DIGITALOCEAN_AC`
- `10s` `cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ && doctl version && doctl registry creat`
- `25s` `npm test 2>&1 | grep -E "^ℹ (pass|fail)" && docker build -q --platform linux/amd64 -t registry.digitalocean.com/adb-pzps1-realtime/adb-pzps1-realtime-web:v1 . && docker push -q registry.digitalocean.c`
- `59s` ❌ `doctl apps list --format ID,DefaultIngress,ActiveDeployment.Phase,InProgressDeployment.Phase`
- `1m 03s` `doctl apps list -o json | jq '.[] | {id, default_ingress, a: .active_deployment.phase, p: .in_progress_deployment.phase, region: .region.slug}'`
- `1m 13s` `U=https://adb-pzps1-realtime-nd5yo.ondigitalocean.app`
- `1m 23s` `cat > deployment.json <<'EOF'`
