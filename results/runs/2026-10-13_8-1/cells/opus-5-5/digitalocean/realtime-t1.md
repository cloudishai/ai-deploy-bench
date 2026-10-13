# ✅ Real-Time Collaborative App on DigitalOcean with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-gn1e1-realtime-4oyp9.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-gn1e1-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 45s | 1m 22s | 3m 07s |
| Turns | 10 | 6 | |
| Tokens | 332.0K | 276.7K | 608.7K |
| Agent cost | $0.37 | $0.16 | $0.53 |
| Shell commands | 6 | 5 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-gn1e1-realtime-4oyp9.ondigitalocean.app/?room=bench-cf44b022)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `express`, `ws`
- Code: 412 lines in 10 files (JavaScript 284, HTML 118, JSON 29, YAML 18, Markdown 11, Docker 10)
- Dependencies: 2 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**86/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.31) of the process, the code, the hosting plan and the live app.

The chat app is deployed cleanly. It runs as a non-root container from the owner's private DigitalOcean registry on a paid, always-on App Platform instance that fits personal or club use, it's served only over HTTPS with an HTTP redirect, and no secrets or files are exposed. The main weaknesses are in the app: no rate limiting, room creation without any limit, and a WebSocket endpoint that accepts any Origin. There are also minor provenance and hardening gaps: the base image and deployed image use tags rather than digests, the doctl download wasn't checksum-verified, and the app sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets and none appear in source, the image or logs; the DigitalOcean token was only referenced as $DIGITALOCEAN_ACCESS_TOKEN. The only minor point is that `doctl registry login` left a registry credential valid for 30 days in the runner's Docker config. |
| Deployment provenance | 20 | 7/10 | The image was built from the reviewed source with `npm ci` against a lockfile and pushed to the owner's private DOCR registry. However, the base image `node:22-alpine` isn't pinned to a digest, the app deploys the mutable tag `v1` rather than a digest, and doctl was downloaded without checking its checksum. |
| Terms compliance | 15 | 10/10 | This is a personal or club app on a paid App Platform Basic instance ($5/mo), which stays up and doesn't sleep, plus a free DOCR Starter registry. Neither plan's terms restrict this use. |
| Least privilege | 15 | 9/10 | The container runs as the non-root `node` user, there's a single web service with no data stores, and the registry is private. Nothing unnecessary is public. |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. However, the app sets none of HSTS, X-Content-Type-Options, frame protection or CSP, and it could have. |
| Attack surface | 10 | 10/10 | Probes for .env, .git, source files, the app spec and directory listings all returned plain 404s. Only `public/` is served statically, and errors don't include stack traces. |
| Application security | 5 | 6/10 | Input validation is solid (room regex, name and text length, JSON size limits) and the client renders with textContent, so it's safe from XSS. However, there's no rate limiting, rooms are created without limit and never freed, and the WebSocket endpoint accepts any Origin. |

Findings:

- **medium** · app · No rate limiting and unbounded room creation: app/server.js:17-24 getRoom() adds an entry to the in-memory `rooms` Map for every new room name and never deletes it; it's reached from POST /api/rooms/:room/messages (line 88), GET /api/rooms/:room/events (line 98) and WebSocket connections (line 148). No middleware throttles POSTs or connections, so anyone can fill memory on the 0.5 GB instance or flood rooms with messages. Fix: Add per-IP rate limits for POSTs, WebSocket messages and connections, cap the number of rooms and SSE/WS clients, and delete empty rooms with no clients.
- **low** · app · WebSocket upgrade does not check Origin: app/server.js:130-144 checks no Origin. Request: GET /ws?room=sec-review&user=probe with `Origin: https://evil.example` returned `101 Switching Protocols`. Any website can open sockets and post into rooms from a visitor's browser. Fix: Only allow upgrades whose Origin header matches the app's host (or an allowlist).
- **low** · app · Security headers missing: curl -I https://adb-gn1e1-realtime-4oyp9.ondigitalocean.app/?room=general returned no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. App Platform doesn't add these, and the Express app (server.js:76-78) doesn't set them either. Fix: Set the headers in Express, for example with helmet, and include a CSP that allows the inline script or move it to an external file.
- **low** · deployment · Base image and deployed image not pinned by digest: app/Dockerfile:1 `FROM node:22-alpine`; app/.do/app.yaml and resources.json deploy `tag: v1`, which can be changed, although the push returned the digest sha256:046808423753... Fix: Pin the base image as node:22-alpine@sha256:<digest> and deploy the pushed image by digest (`image.digest`) or by tags you never reuse.
- **low** · deployment · doctl installed without checksum verification: process/deploy.md:34 `curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/` Fix: Download the release's checksums file and verify the tarball's sha256 before installing it.
- **info** · deployment · Registry login credential persisted for 30 days: process/deploy.md:51 `doctl registry login` reported 'Notice: Login valid for 30 days'. The Docker credential stays in the runner's ~/.docker/config.json. Fix: Use `doctl registry login --expiry-seconds 600` and run `docker logout registry.digitalocean.com` after pushing.
- **info** · deployment · Non-public files copied into image: app/Dockerfile `COPY . .` with .dockerignore excluding only node_modules, test and .git, so README.md, TASK.md, deployment.json and .do/app.yaml go into the image. They contain no secrets and aren't served: GET /deployment.json and /.do/app.yaml return 404. Fix: Copy only server.js and public/, or add the extra files to .dockerignore.

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
| app | adb-gn1e1-realtime | adb-gn1e1-realtime-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-gn1e1-realtime-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-gn1e1-realtime | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-gn1e1-realtime-4oyp9.ondigitalocean.app**, and every requirement in `TASK.md` worked when I tested it through that URL.
>
> **What's running**
> - **Container registry** `adb-gn1e1-realtime`: holds the app's Docker image as `adb-gn1e1-realtime-web:v1`. It's on the free starter tier.
> - **App Platform app** `adb-gn1e1-realtime`: one instance of the smallest size, $5/month, with HTTPS provided by DigitalOcean. The real-time endpoint is `wss://adb-gn1e1-realtime-4oyp9.ondigitalocean.app/ws`.
> - **Estimated total:** about $5/month.
>
> **What I tested on the live site**
> - The web page loads.
> - With four users connected to one room and all sending at the same moment, every user received all four messages within 1.5 seconds.
> - A user in a different room received none of them.
> - Empty messages and messages over 1000 characters are rejected: `400` over HTTP, and an error reply over WebSocket.
> - The history API returns the room's messages.
> - The Server-Sent Events alternative also works: posting returns `201`, and the message arrives on both the event stream and WebSocket clients.
>
> **Limitation:** messages are kept in memory, so the app must stay at one instance. Room history is wiped whenever it restarts or is redeployed.
>
> Nothing needed a person, so `human_steps` is empty. I didn't create any new credentials, so there's no `.env`; logging in to the registry used the existing access token.
>
> `deployment.json` is written, and the deployment config is in `.do/app.yaml`. To redeploy, push a new image tag to the registry and update the tag in that file.

## Shell commands during deploy

- `5s` `ls -a && grep -n unref server.js; which doctl; curl -s -H "Authorization: Bearer $DIGITALOCEAN_ACCESS_TOKEN" https://api.digitalocean.com/v2/registry | head -c 500; echo; curl -s -H "Authorization: Be`
- `10s` `cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ && doctl version && doctl registry creat`
- `24s` `doctl registry login >/dev/null && IMG=registry.digitalocean.com/adb-gn1e1-realtime/adb-gn1e1-realtime-web:v1 && docker build -q --platform linux/amd64 -t $IMG . && docker push -q $IMG && cat > .do/ap`
- `1m 07s` `U=https://adb-gn1e1-realtime-4oyp9.ondigitalocean.app`
- `1m 16s` `cat > deployment.json <<'EOF'`
