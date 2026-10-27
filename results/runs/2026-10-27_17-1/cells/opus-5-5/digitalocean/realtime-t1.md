# ✅ Real-Time Collaborative App on DigitalOcean with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-w4mhs-realtime-mplbp.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-w4mhs-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 39s | 1m 51s | 4m 22s |
| Turns | 9 | 5 | |
| Tokens | 343.9K | 264.1K | 847.9K |
| Agent cost | $0.39 | $0.13 | $0.69 |
| Shell commands | 8 | 4 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 52s, 239.9K tokens, $0.17).

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-w4mhs-realtime-mplbp.ondigitalocean.app/?room=bench-29c2323f)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Runtime: Node.js 20
- Frameworks: Node.js http module (built in)
- Libraries: ws
- Packaging: Docker (node:20-alpine), App spec (.do/app.yaml)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 442 lines in 13 files (JavaScript 274, HTML 114, Shell 44, Markdown 32, JSON 32, YAML 16, Docker 10)
- Dependencies: 1 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

### Stack fit

**79/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A minimal Node.js and ws server on a single App Platform instance fits a club chat well and follows the reasoning in STACK.md. Its main weakness is in-memory history, which is lost on every restart or redeploy and keeps the app on one instance.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 7/10 | Node with ws is a good match for WebSocket fan-out with room isolation, and the latency target is easily met. Keeping history in memory isn't durable: it resets on every redeploy or restart, which STACK.md acknowledges. TASK.md asks only for recent history, so this is a weakness rather than a failure. |
| Proportion | 30 | 9/10 | There is one source file, one runtime dependency and no framework or extra services, about as simple as the requirements allow. The rejected Redis and Droplet alternatives are reasonably argued in STACK.md. |
| Platform fit | 30 | 8/10 | App Platform's always-on web service, managed TLS, WebSocket support and health checks suit a long-lived socket server. The app is pinned to one instance because state lives in memory, and building a Docker image locally and pushing it to DOCR is more manual than App Platform's own source builds. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**84/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.32) of the process, the code, the hosting plan and the live app.

This small Node.js and ws chat app on DigitalOcean App Platform is deployed cleanly. The token was kept out of the code, image and logs; the container runs as a non-root user; HTTPS redirects and wss:// work; probing found no exposed files; and input validation and XSS handling are sound. The main weaknesses are provenance (a locally built image deployed by the mutable :latest tag, an unpinned base image, and doctl installed without checksum verification) and missing security headers and abuse limits.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The DigitalOcean token came from an environment variable and never went into source, the image (.dockerignore excludes .env), or the logs, because deploy output was piped through `grep -v -i token`. The app needs no runtime secrets. One minor issue: deploy.sh passes the token to `doctl auth init -t` on the command line. |
| Deployment provenance | 20 | 6/10 | The image was built on the agent's machine and pushed to the owner's private DOCR, and the app references the mutable `:latest` tag rather than a digest. The base image `node:20-alpine` isn't digest-pinned, and doctl is downloaded with curl and installed without checksum verification. Dependencies are locked through package-lock.json and `npm ci`. |
| Terms compliance | 15 | 10/10 | This is a personal club app on a paid App Platform Basic instance ($5/month) that stays always on, with the free DOCR Starter tier well under its limits. Nothing in DigitalOcean's terms conflicts with this use. |
| Least privilege | 15 | 9/10 | The container runs as the non-root `node` user, there is no data store to expose, the registry is private, and only one public web service exists. It is close to minimal, although the image keeps npm and the rest of the full Alpine Node toolchain. |
| Transport security | 10 | 8/10 | HTTPS uses a valid Google Trust Services certificate, HTTP gets a 301 redirect to HTTPS, and WebSockets use wss://. The app sends no HSTS, CSP, X-Content-Type-Options or frame-protection headers even though it controls all of its responses. |
| Attack surface | 10 | 10/10 | Probes for .env, .git/config, server.js, package.json, Dockerfile and unknown paths all return a JSON 404. Errors return short JSON with no stack traces, and the only extra endpoint is /healthz, which returns {"ok":true}. |
| Application security | 5 | 7/10 | Validation is solid: text must be 1-1000 characters, user names 1-50, room names are restricted to [A-Za-z0-9_-], request bodies are capped at 16 KB, WebSocket payloads are capped, and the UI renders with textContent, which prevents XSS. There is no rate limiting, no cap on the number of rooms or connections, and no Origin check on WebSocket upgrades, so the public endpoints are easy to spam or use to fill memory. |

Findings:

- **medium** · deployment · Deployed by a mutable :latest tag from a local build: app/.do/app.yaml: `tag: latest`; deploy.sh builds locally and runs `docker push registry.digitalocean.com/$REG/adb-w4mhs-realtime-web:latest`. The pushed digest sha256:5a8c30ef... (process/deploy.md) isn't recorded in the spec. Fix: Deploy by image digest or an immutable tag such as the git SHA, ideally built by CI from a repository the owner controls.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile:1 `FROM node:20-alpine` Fix: Pin the base image, for example `node:20-alpine@sha256:...`, and update it deliberately.
- **low** · deployment · doctl installed without checksum verification: deploy.sh and process/deploy.md: `curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz -C /tmp && sudo mv /tmp/doctl /usr/local/bin/` Fix: Verify the release checksum file before installing, or use a package manager or the official GitHub Action.
- **low** · app · No rate limiting or room/connection caps: app/server.js:17-24 `getRoom` creates a room for any valid name on every POST, SSE or WS connection, with no limit on the number of rooms; app/server.js:103-110 and 150-158 accept unlimited messages. Fix: Add per-IP or per-connection message rate limits, cap the number of rooms and connections, and drop empty rooms.
- **low** · app · WebSocket upgrade has no Origin check: app/server.js:132-139 validates only the path, room and user, never `req.headers.origin`. Fix: Reject upgrades whose Origin isn't the app's own host. The impact is limited because there is no authentication.
- **low** · app · No security headers: `curl -D - https://adb-w4mhs-realtime-mplbp.ondigitalocean.app/?room=general` returns content-type, cache-control and Cloudflare headers but no Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options or X-Frame-Options; app/server.js:89 sets only Content-Type. Fix: Set HSTS, `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'` and a CSP in the app's response headers.
- **info** · deployment · Token passed as a command-line argument: app/deploy.sh: `doctl auth init -t "$DIGITALOCEAN_ACCESS_TOKEN"` Fix: Let doctl read DIGITALOCEAN_ACCESS_TOKEN from the environment instead of passing it on the command line.
- **info** · app · No sensitive files or debug endpoints exposed: GET /.env, /.git/config, /server.js, /package.json and /Dockerfile all return 404 {"error":"not found"}; GET /healthz returns 200 {"ok":true}. Fix: None needed.

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
| app | adb-w4mhs-realtime | adb-w4mhs-realtime-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-w4mhs-realtime-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-w4mhs-realtime | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The chat app is live on DigitalOcean at **https://adb-w4mhs-realtime-mplbp.ondigitalocean.app**, with WebSockets at `wss://adb-w4mhs-realtime-mplbp.ondigitalocean.app/ws`. Every requirement in `TASK.md` passed when I tested it through that public URL, and nothing needed a person.
>
> **What I tested on the live app:**
> - The page at `/` loads.
> - Posting a message over HTTP returns 201, and an empty or over-1000-character message returns 400.
> - History returns at most 50 messages, oldest first.
> - A WebSocket message reaches everyone in the room, including the sender.
> - A client in another room does not receive it.
> - An invalid WebSocket message gets an error reply.
> - Five clients each sent 10 messages at the same time, and every client received all 50 within about 170 ms (the limit is 2 seconds).
> - The Server-Sent Events stream also delivers messages.
>
> **What I deployed (about $5/month):**
>
> | Resource | Name | Plan | Cost |
> |---|---|---|---|
> | App Platform web service | `adb-w4mhs-realtime` / `adb-w4mhs-realtime-web` (id `2e6ff6eb-d0d9-4339-a589-bc44e3055619`) | 512 MB, one instance, New York region | $5/month |
> | Container Registry | `adb-w4mhs-realtime` | free tier | $0 |
>
> App Platform provides HTTPS and `wss://` itself.
>
> The one change to the files from the last step: `deploy.sh` now runs without a `.env` file, since the token came from an environment variable. I didn't create any new credentials, so there's no `.env`.
>
> **Limitation:** chat history is kept in memory, so it's lost whenever the app restarts or is redeployed. For the same reason the app has to stay at one instance. To redeploy, run `./deploy.sh`; `./smoke.sh <url>` repeats the main checks.

## Shell commands during deploy

- `4s` `test -n "$DIGITALOCEAN_ACCESS_TOKEN" && echo token set; which doctl || (curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz -C /tmp && s`
- `9s` `sed -i 's#^set -a; source .env; set +a#[ -f .env ] \&\& { set -a; source .env; set +a; }#' deploy.sh && ./deploy.sh 2>&1 | grep -v -i token | tail -25`
- `1m 30s` `U=https://adb-w4mhs-realtime-mplbp.ondigitalocean.app; ./smoke.sh $U; curl -s -o /dev/null -w "too long -> %{http_code}\n" -XPOST $U/api/rooms/smoke/messages -H 'content-type: application/json' -d "{\`
- `1m 45s` `doctl registry get --format Name,Region --no-header; cat > deployment.json <<'EOF'`
