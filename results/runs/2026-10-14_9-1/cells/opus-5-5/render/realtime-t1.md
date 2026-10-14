# ✅ Real-Time Collaborative App on Render with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-f30wl-realtime-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-f30wl-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 40s | 1m 33s | 3m 13s |
| Turns | 9 | 7 | |
| Tokens | 339.5K | 338.2K | 677.6K |
| Agent cost | $0.38 | $0.20 | $0.59 |
| Shell commands | 8 | 6 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-f30wl-realtime-web.onrender.com/?room=bench-d8553322)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `ws`
- Code: 402 lines in 8 files (JavaScript 281, HTML 121, JSON 26, Markdown 14, YAML 13)
- Dependencies: 1 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optionally connect a GitHub/GitLab account to Render (or provide a git token) and repoint the service at a repo containi

## Security and compliance review

**78/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.31) of the process, the code, the hosting plan and the live app.

The chat app is small and handles input carefully. It needs no secrets, and the Render API key never leaked. It is served only over valid HTTPS on Render's free plan, which fits a hobby club's personal use. The main weakness is provenance: the service builds from Render's public example repo on an unpinned branch, with the real code smuggled in as a base64 env var, so there's no owner-controlled source of truth. Smaller issues are missing rate limiting and room eviction, no WebSocket Origin check and no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no secrets. The Render API key was only read from $RENDER_API_KEY in curl headers and never printed. The source, the bundle and the env vars hold no credentials. |
| Deployment provenance | 20 | 4/10 | Production does not build from a repo the owner controls. The service points at a third-party public repo (render-examples/express-hello-world, branch main, unpinned). The real code arrives as a base64 tarball in an env var and is unpacked by the build command, so there is no commit or audit trail for what runs. The lockfile and npm ci do pin dependencies. |
| Terms compliance | 15 | 8/10 | This is personal (hobby club) use on Render's free plan, which as I understand its terms allows hobby projects. The free instance sleeps after about 15 minutes idle and loses all in-memory history when it does. The agent documented this, and it is tolerable for a club chat but a real limitation. |
| Least privilege | 15 | 9/10 | There is one public web service and no data stores or extra resources. It runs on Render's managed Node runtime rather than a custom root container. Pointing the service at a public third-party repo is the main oddity. |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate, HTTP 301-redirects to HTTPS, and the WebSocket uses wss. The app sets no HSTS, X-Content-Type-Options, frame-protection or CSP headers, and Render does not add them. |
| Attack surface | 10 | 9/10 | Only the app's routes respond; .env, .git, source files and leftover template files return JSON 404s, with no stack traces or directory listings. /healthz is public but harmless. A malformed percent-encoded path gets the edge proxy's generic HTML 400 page. |
| Application security | 5 | 6/10 | Input validation is solid: text length, user and room length, body and WebSocket payload size limits, and textContent rendering with no XSS. But there is no rate limiting. The room map grows without bound because empty rooms are never evicted, SSE streams are uncapped, and WebSocket upgrades don't check Origin. |

Findings:

- **medium** · deployment · Deployed from a third-party public repo with code injected via an env var: process/deploy.md service create body: "repo":"https://github.com/render-examples/express-hello-world","branch":"main", envVars APP_BUNDLE_B64=<tarball>, buildCommand "rm -rf node_modules package.json package-lock.json yarn.lock && echo \"$APP_BUNDLE_B64\" | base64 -d | tar xz && npm ci --omit=dev"; process/resources.json source: render-examples/express-hello-world Fix: Push the app to a repo the owner controls and connect it to Render (or deploy a digest-pinned image from the owner's registry), so production maps to a reviewable commit.
- **medium** · app · No rate limiting and unbounded room/stream growth: app/server.js:16-23 creates a room for any name (including on GET /events, line 127) and never deletes it; lines 116-124 and 170-178 have no per-client rate limit; line 135 has no cap on SSE streams Fix: Add per-IP/per-socket rate limits, cap rooms and connections, and evict empty rooms that have no history.
- **low** · deployment · Build source branch unpinned and runtime version only major-pinned: Branch 'main' of an external repo is checked out at build time (HEAD 039c3477… observed, not pinned); NODE_VERSION="22" (app/render.yaml, deploy body) Fix: Pin the source commit and an exact Node version (e.g. 22.x.y) or an engines range plus .node-version.
- **low** · deployment · Free instance sleeps and loses in-memory history: process/deployment.json notes: 'free plan spins down after ~15 min idle'; app/server.js:14 keeps rooms in a process-local Map Fix: Accept it for a hobby club, or move to a paid starter instance with a small persistent store (Render Key Value or Postgres) if history must survive restarts.
- **low** · app · WebSocket upgrade does not validate Origin: Request: GET /ws?room=review-probe&user=reviewer with Origin: https://evil.example -> HTTP/1.1 101 Switching Protocols; app/server.js:147-160 has no Origin check Fix: Reject upgrades whose Origin isn't the app's own host.
- **low** · app · No identity: any client can post as any display name: app/server.js:120 and 150 take the user name verbatim from the request body or query Fix: Acceptable per spec for a club app. Optionally add a shared room passcode or a session token so names can't be spoofed.
- **low** · app · Missing security headers: curl -D- https://adb-f30wl-realtime-web.onrender.com/ returns only content-type, cache-control and the Cloudflare/Render headers: no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy Fix: Set HSTS, nosniff, frame-ancestors 'none' and a restrictive CSP in server.js responses.
- **info** · platform · Edge proxy returns its own HTML error for malformed paths: GET /api/rooms/%E0%A4%A/messages -> 400 with nginx-style '<title>400 Bad Request</title>' HTML Fix: None needed; it reveals no sensitive information.
- **info** · deployment · API key handled via environment only: process/deploy.md: curl -H "Authorization: Bearer $RENDER_API_KEY" …; the key is never echoed and no .env was created Fix: None.

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
| service | adb-f30wl-realtime-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-f30wl-realtime-web.onrender.com**, and every requirement worked when I tested it through the public URL.
>
> **What I deployed:** one Render web service, `adb-f30wl-realtime-web` (`srv-db7etjd9fdbs73dvv4eg`), on the free plan in Oregon. It costs $0 a month. The real-time address is `wss://adb-f30wl-realtime-web.onrender.com/ws`.
>
> **Public test results:**
> - `GET /` serves the chat page.
> - Two WebSocket users each sent 5 messages at the same time, and one more was posted over HTTP. All 11 reached both users in about 0.4 seconds.
> - A user in a different room received none of those messages.
> - Over HTTP, valid messages return `201` and empty or 1001-character messages return `400`. An empty WebSocket message got an error reply.
> - The history endpoint returned the room's messages, oldest first.
> - The Server-Sent Events stream delivered a posted message.
>
> **How the code got there:** there were no GitHub credentials, so I couldn't push this project to a repo for Render to build from. Instead, the service points at Render's public example repo (`render-examples/express-hello-world`) only to get a build started. Its build command throws away that repo's package files and unpacks this app from a compressed copy stored in an environment variable, `APP_BUNDLE_B64`. Everything still runs on Render. To ship a change, regenerate that variable and redeploy; `deployment.json` has the exact command. Connecting a GitHub account to Render would allow normal deploys from a repo; I listed that as an optional, non-blocking step under `human_steps`.
>
> **Limitations:**
> - Messages are kept in memory, so history is lost whenever the service restarts or redeploys.
> - The free plan sleeps after about 15 minutes with no traffic. The first visit after that takes roughly 30–60 seconds to wake it up.
>
> I didn't create any credentials, so there is no `.env` file.

## Shell commands during deploy

- `5s` `cd /home/runner/work/_temp/adb-f30wl-realtime; gh auth status 2>&1 | head -5; env | grep -iE 'github|gh_' | sed 's/=.*/=***/'; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com`
- `19s` `git archive HEAD server.js package.json package-lock.json public | gzip -9 | base64 -w0 > /tmp/app.b64 && wc -c /tmp/app.b64; git ls-remote https://github.com/render-examples/express-hello-world HEAD`
- `25s` `python3 - > /tmp/body.json <<'EOF'`
- `30s` `for i in $(seq 1 40); do s=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-db7etjd9fdbs73dvv4eg/deploys/dep-db7etjl9fdbs73dvv5s0 | python3 -c "import json,s`
- `1m 10s` `U=https://adb-f30wl-realtime-web.onrender.com`
- `1m 25s` `cat > deployment.json <<'EOF'`
