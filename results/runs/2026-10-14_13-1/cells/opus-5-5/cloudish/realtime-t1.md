# ✅ Real-Time Collaborative App on Cloudish with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-bysca-realtime.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $0.41)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-bysca-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 43s | 4m 04s | 6m 46s |
| Turns | 16 | 13 | |
| Tokens | 599.5K | 812.5K | 1.41M |
| Agent cost | $0.54 | $0.38 | $0.92 |
| Shell commands | 10 | 11 | |

App answered 0s after the agent finished deploying.

**Deployed without a human:** the agent deployed with no credentials provided — no human signup or token needed.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-bysca-realtime.on.do.cloudish.ai/?room=bench-383b8aef)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Runtime: Node.js 24
- Frameworks: Node.js http module (built in)
- Data: SQLite (on a persistent volume)
- Libraries: ws
- Packaging: Docker (node:24-slim)
- Hosting: Cloudish container (shared) with a persistent volume
- Code: 474 lines in 10 files (JavaScript 351, HTML 112, Markdown 42, JSON 30, Docker 11)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Node.js 24 with ws and node:sqlite in a single Dockerfile container, with a persistent volume, is a minimal, well-reasoned fit for a small realtime chat on a container platform, and the build matched STACK.md.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | Native WebSockets via `ws` suit the realtime requirement, and SQLite on a persistent volume gives durable history. The plain HTML/JS client is served by the same process. SSE was added cheaply from the same broadcast hub. |
| Proportion | 30 | 9/10 | One process and one runtime dependency, using built-in node:sqlite with no build step. Nothing is extraneous, and there are no fake stand-ins for a database. |
| Platform fit | 30 | 9/10 | Cloudish runs long-lived containers that support WebSockets, with opt-in volumes and no managed database. A single container with SQLite on a volume is exactly what it supports, and scale-to-zero keeps costs low. The single-replica limit that the volume forces is acceptable for a club. |

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-bysca-realtime' (mint a claim link with GET https://cloudish.ai/api/v1/credits/claim using t

## Security and compliance review

**86/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.35) of the process, the code, the hosting plan and the live app.

A small, carefully built Node.js/ws/SQLite chat app, deployed as a non-root container built server-side from its own source with a lockfile. Secrets never leaked, and nothing beyond the app is exposed. The main weaknesses are no rate limiting or storage bounds on the public endpoints, missing app-set security headers, a tag-only base image, and a free credit grant that will stop the app within hours unless the owner adds credits.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to .env without being printed (`jq 'del(.key, .claimUrl)'`). .env* was left out of both the upload tarball and .dockerignore. The app itself needs no secrets. |
| Deployment provenance | 20 | 8/10 | Cloudish built the image on its servers from a tarball of the agent's own source, and `npm ci` installed from the committed lockfile. The deploy log shows the build succeeded and the image tag running. The base image `node:24-slim` is pinned by tag only, not by digest. |
| Terms compliance | 15 | 7/10 | This is a personal club app on a prepaid-credit container platform. I know of no terms that rule out this use, though I couldn't confirm Cloudish's terms. The free 0.1-credit grant covers only about 9 hours of runtime, so the app will stop until a person claims the key and adds credits. The agent disclosed this, but marked it non-blocking. |
| Least privilege | 15 | 9/10 | The container runs as the non-root `node` user, and the SQLite volume is private and mounted only at /data. The only public resource is the web service, which is intentional. The project's `access: open` is what a public chat needs. |
| Transport security | 10 | 8/10 | Traffic is HTTPS only, with a valid Let's Encrypt certificate, HSTS, and an HTTP→HTTPS 308 redirect, all from the platform. The app sets no X-Content-Type-Options, frame protection or CSP, and it could have. |
| Attack surface | 10 | 10/10 | Probes for .env, .git/config, server.js, package.json, Dockerfile, /data/chat.db and /public/* all returned a generic JSON 404. Errors return short JSON with no stack traces, and only the app's own endpoints plus /healthz are reachable. |
| Application security | 5 | 7/10 | Validation is solid: lengths, types, a 16 KB body cap and WebSocket maxPayload. SQL queries are parameterized, and the UI renders with textContent, so there is no XSS. The public endpoints have no rate limiting or Origin check, so anyone can flood rooms. Storage is unbounded, which could fill the 1 GB volume and drain credits. |

Findings:

- **medium** · app · No rate limiting or storage bounds on public message endpoints: server.js:144-152 and 201-212 accept any number of POSTs and WebSocket messages, and server.js:39 stores every message forever. Any room name up to 64 characters is accepted (server.js:47), so a script can create unlimited rooms and fill the 1 GB volume. Fix: Add per-IP and per-connection rate limits, and prune old messages per room (for example keep the last N). Consider capping how many distinct rooms can be created.
- **medium** · deployment · Free credit grant runs out after about 9 hours: process/deployment.json human_steps: 'The free 0.1-credit grant covers only ~9 hours of container runtime; after that requests return 402/503'. process/context.json shows a balance of 0.097. Fix: Have the owner claim the key and add credits before the club relies on the app, and treat this as a blocking step.
- **low** · app · WebSocket upgrade does not check Origin: A WebSocket upgrade to /ws?room=review&user=tester with `Origin: https://evil.example` got HTTP 101. server.js:184-192 checks only path, room and user. Fix: Allow only the app's own origin on upgrade. The impact is small because there is no authentication, but it stops other sites from driving users' browsers into posting.
- **low** · app · Missing browser security headers: `GET /` returns only content-type, cache-control and strict-transport-security (HSTS comes from the platform). There is no X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. server.js:131 sets only content-type and cache-control. Fix: Set `X-Content-Type-Options: nosniff`, `Content-Security-Policy` (with frame-ancestors 'none') and `Referrer-Policy` in the response helpers.
- **low** · deployment · Base image pinned by tag only: app/Dockerfile:1 `FROM node:24-slim` Fix: Pin the base image by digest (`node:24-slim@sha256:...`) so rebuilds are reproducible.
- **info** · app · Display names can be impersonated: server.js:148 and 188 take `user` from the request body or query string with no authentication. TASK.md asks only for a display name. Fix: This is acceptable for a hobby club as specified. If impersonation matters, add a lightweight shared room passphrase or per-session tokens.
- **info** · deployment · API key kept out of logs and the build context: process/deploy.md: the key-creation command writes .key to .env and prints `jq 'del(.key, .claimUrl)'`. The tarball was built with `--exclude='.env*'`, and its listing has no .env. Fix: No action needed.

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
| project | adb-bysca-realtime-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live on Cloudish at **https://adb-bysca-realtime.on.do.cloudish.ai**, and every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What's deployed:**
> - **API key** `adb-bysca-realtime`: I created it myself; it's saved in `.env`, which the build excludes.
> - **Container app** `adb-bysca-realtime-web`: Cloudish built it on its own servers from the Dockerfile. It runs on the cheapest size (`shared`) and sleeps after 15 minutes with no requests.
> - **1 GB persistent disk** mounted at `/data`, so chat history in SQLite survives restarts and sleep. Disks aren't billed.
> - **Subdomain** with a valid Let's Encrypt certificate. The first few requests failed until the certificate was issued, then worked. The original random URL is no longer active.
>
> **Tested through the public URL:**
> - **Page:** `GET /` returns 200.
> - **History API:** returns the room's messages, oldest first.
> - **HTTP posting:** `POST` returns 201, and 400 for empty or over-1000-character text.
> - **Live updates:** 4 users each sent 5 messages at the same time over WebSocket. Every user got all 20 in under 100 ms.
> - **Rooms and validation:** a user in another room received nothing, and invalid WebSocket messages got an `error` reply.
> - **Server-Sent Events:** the stream received posted messages.
> - **Idle connections:** an idle WebSocket was still open after 70 seconds.
>
> **Cost:** about $0.0107 per hour while the app is running, roughly $0.41/month at an hour of use a day. `deployment.json` records the URL, `"realtime": {"transport": "websocket", "url": "wss://adb-bysca-realtime.on.do.cloudish.ai/ws"}`, the resources and this estimate.
>
> **Two things to know:**
> - **Credits will run out.** The free grant is $0.10, about 9 hours of running time; the balance was $0.097 when I finished. Once it's used up, the app returns 402/503 until a person claims the key and adds credits. That's listed under `human_steps` (not blocking for now).
> - **Waking from sleep:** the first request after 15 idle minutes waits a few seconds while the container starts. Open chat connections drop when it sleeps, and the web page reconnects on its own.

## Shell commands during deploy

- `19s` `curl -s https://cloudish.ai/skill.md`
- `25s` `test -f .env && grep -c CLOUDISH .env; `
- `29s` `set -a && . ./.env && set +a`
- `38s` `. ./.env`
- `1m 39s` `. ./.env`
- `1m 43s` `. ./.env`
- `1m 54s` `U=https://adb-bysca-realtime.on.do.cloudish.ai`
- `2m 03s` `curl -s -o /dev/null -w 'random %{http_code}\n' https://f730baaedbf112282dc79b92c78d24f3.on.do.cloudish.ai/`
- `2m 19s` `U=https://adb-bysca-realtime.on.do.cloudish.ai`
- `2m 32s` `timeout 90 node -e "`
- `3m 54s` `. ./.env && curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq '.runway // .apiKey.balance'`
