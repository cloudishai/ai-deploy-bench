# ✅ Real-Time Collaborative App on Render with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-mlvy1-realtime-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-mlvy1-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 43s | 1m 41s | 4m 20s |
| Turns | 9 | 7 | |
| Tokens | 347.9K | 393.9K | 986.1K |
| Agent cost | $0.41 | $0.23 | $0.83 |
| Shell commands | 8 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 56s, 244.3K tokens, $0.19).

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-mlvy1-realtime-web.onrender.com/?room=bench-28a7919a)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Runtime: Node.js 18+
- Frameworks: Node.js http module (built in)
- Libraries: ws
- Packaging: Render Blueprint (render.yaml)
- Hosting: Render web service (free, built from render-examples/express-hello-world)
- Code: 481 lines in 12 files (JavaScript 339, HTML 125, Markdown 36, JSON 27, Shell 17, YAML 9)
- Dependencies: 1 npm, 0 Python
- Deploy config: `render.yaml`

### Stack fit

**76/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Node with `ws` on a single Render web service is a proportionate, well-reasoned choice for realtime chat. Its weak spot is in-memory history, which, combined with the free plan's sleep, means history doesn't persist; adding Render Key Value or Postgres would fix that.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 7/10 | Node with `ws` on a long-running web service is a good fit for WebSocket fan-out, and SSE support comes almost for free. However, in-memory history is not durable and is wiped on every restart and every free-plan sleep, which undermines the 'recent history' requirement. |
| Proportion | 30 | 9/10 | There is one process and one dependency, and the HTML is served by the same server. This is about as minimal as the requirements allow, and STACK.md reasons soundly about deferring Postgres or Redis. |
| Platform fit | 30 | 7/10 | A Render web service supports WebSockets natively and suits this app. The free plan's spin-down works against long-lived connections and in-memory state, and the env-var bundle workaround bypasses Render's Git-based deploy flow. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optional: push this repo to a GitHub/GitLab repo named adb-mlvy1-realtime, connect it to Render, and point adb-mlvy1-rea

## Security and compliance review

**78/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.38) of the process, the code, the hosting plan and the live app.

The club chat app is small and well-validated. It runs as a single Render free web service with no secrets, renders messages without XSS risk, and exposes no files or debug endpoints. Its main weaknesses are in how it was deployed: the live code arrives as a base64 tarball in an env var on top of a third-party placeholder repo, so the deployment has no owner-controlled source. The free plan also sleeps, and each spin-down wipes the in-memory history. There is no rate limiting and no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no secrets. The Render API key stayed in the agent's environment and was never printed or committed, `.env` is git-ignored, and the only env vars set on the service are APP_BUNDLE (app code, not a secret) and NODE_VERSION. |
| Deployment provenance | 20 | 5/10 | The service's source is a third-party public repo (render-examples/express-hello-world). Its build command deletes that checkout and unpacks the real app from a base64 tarball in an env var, so Render's deploy record points at code that never runs and the live code has no owner-controlled, auditable source. The dependencies are pinned well (lockfile plus `npm ci`, a single dependency), but Node is pinned only to major version 22. |
| Terms compliance | 15 | 6/10 | A hobby club's personal app is an acceptable use of Render's free plan. However, free web services spin down after about 15 minutes idle, and because history is kept in memory, every spin-down wipes the room history the spec requires, and the first visitor waits about a minute. The agent disclosed this but did not mitigate it. |
| Least privilege | 15 | 9/10 | There is a single public web service on Render's managed Node runtime, with no data stores or extra resources and no privileged settings. The only access-related gap is that the WebSocket endpoint accepts upgrades from any Origin, which matters little for an app without authentication. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Google Trust Services certificate, and HTTP gets a 301 redirect to HTTPS. However, neither Render nor the app sets HSTS, X-Content-Type-Options, frame protection or CSP, and the app could easily have added them. |
| Attack surface | 10 | 10/10 | Only `/`, `/healthz`, the API and `/ws` respond. Probes for `/.env`, `/.git/config`, `/package.json`, `/server.js` and `/admin` all return a generic JSON 404, and malformed input gets clean 400s with no stack traces. |
| Application security | 5 | 6/10 | Input validation is solid: text length, name and room limits, a 16 KB body cap and WebSocket maxPayload. Messages are rendered with textContent, so they can't inject script. However, there is no rate limiting or connection cap, and rooms are never evicted, so anonymous clients can flood rooms or grow memory without bound. |

Findings:

- **medium** · deployment · Production code delivered via env-var tarball over a third-party placeholder repo: process/deploy.md: service created with repo "https://github.com/render-examples/express-hello-world" and buildCommand 'find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && echo "$APP_BUNDLE" | base64 -d | tar xz && npm ci'; process/resources.json source = render-examples/express-hello-world; app/scripts/deploy.sh line 10-11 PUTs a new APP_BUNDLE. Fix: Push the app to a repo the owner controls and connect it to the service, or deploy a prebuilt image from the owner's registry. Then remove APP_BUNDLE so that Render's deploy record matches the running code.
- **medium** · deployment · Free plan sleeps and in-memory history is lost on every spin-down: app/render.yaml `plan: free`; app/store.js keeps messages in a Map; process/deployment.json notes: 'The free plan sleeps after about 15 minutes idle; the first request after that takes about a minute and history is wiped.' Fix: Use a paid always-on instance (Starter), or store history in a durable store such as Render Postgres or Key Value, so the club's recent history survives idle periods and redeploys.
- **medium** · app · No rate limiting and unbounded room creation: app/server.js: POST /api/rooms/<room>/messages and WS 'message' handler have no per-client throttling; app/store.js `rooms` Map never deletes rooms, so any number of distinct room names each retain up to 50 messages. Fix: Add per-IP or per-connection rate limits and a cap on connections. Bound the number of rooms, for example with LRU eviction of idle rooms.
- **low** · app · Missing security headers: GET https://adb-mlvy1-realtime-web.onrender.com/ response headers: content-type, cache-control, server: cloudflare, x-render-origin-server; no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. Fix: Set HSTS, `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'` and a restrictive CSP in sendJson and in the index response.
- **low** · app · WebSocket upgrade does not check Origin: curl --http1.1 upgrade to /ws?room=reviewtest&user=reviewer with `Origin: https://evil.example` returned `HTTP/1.1 101 Switching Protocols`; app/server.js upgrade handler validates only path/room/user. Fix: Reject upgrades whose Origin is not the app's own host. Without authentication the impact is small, but it stops other sites from driving the chat through visitors' browsers.
- **low** · deployment · Node runtime pinned only to major version: process/deploy.md envVars NODE_VERSION="22"; app/package.json engines "node": ">=18". Fix: Pin an exact Node version (e.g. 22.x.y) through NODE_VERSION or .node-version.
- **info** · app · User content rendered safely: POST {"user":"<img src=x>","text":"<script>alert(1)</script> review probe"} returned 201; app/public/index.html lines 74-75 render messages with textContent. Fix: None needed.
- **info** · app · No exposed files or debug endpoints: GET /.env, /.git/config, /package.json, /server.js, /render.yaml, /admin -> 404 {"error":"not found"}; malformed JSON -> 400 {"error":"invalid JSON body"}. Fix: None needed.

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
| service | adb-mlvy1-realtime-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The chat app is live at **https://adb-mlvy1-realtime-web.onrender.com**, and every requirement passed when I tested it through that public URL.
>
> - **What's deployed:** one Render web service, `adb-mlvy1-realtime-web` (`srv-dbfrheec6qcc73emce4g`), on the free plan in Oregon with Node 22. Estimated cost is $0 a month.
> - **Real-time:** WebSocket at `wss://adb-mlvy1-realtime-web.onrender.com/ws`. The Server-Sent Events endpoint also works: it returned `200` with `text/event-stream`.
> - **Test results:** `scripts/smoke.js` passed every check. The page loads; 9 messages sent at once from 3 clients reached all 3 in about 100 ms; messages have the right shape; rooms stay isolated; an over-long WebSocket message gets an error reply; posting over HTTP returns `201` (or `400` when invalid) and appears live on WebSocket clients; history comes back oldest first. `/healthz` returns ok.
>
> **How the code got there:** no GitHub credentials were available, so I couldn't push this repo anywhere for Render to build from. The service instead points at Render's public example repo (`render-examples/express-hello-world`) with auto-deploy off. Its build command deletes that checkout and unpacks this app's code, which I passed in as a 7.5 KB compressed bundle in the `APP_BUNDLE` env var. It works, but it's a workaround. `deployment.json` lists one optional, non-blocking human step: push the repo to GitHub, connect it to Render and drop `APP_BUNDLE`.
>
> **Redeploying:** I rewrote `scripts/deploy.sh` to update the bundle and trigger a deploy, but I haven't run it since the rewrite. The live deploy was created by a direct API call.
>
> **Limitations:**
> - History is kept in memory (latest 50 per room). It resets on every restart or redeploy, and the service has to stay at a single instance.
> - The free plan sleeps after about 15 minutes with no traffic. The first request after that takes about a minute, and history is wiped.
>
> `deployment.json` and the deploy script are committed. `.env` is git-ignored, and no secrets were printed or written to committed files.

## Shell commands during deploy

- `6s` `cd /home/runner/work/_temp/adb-mlvy1-realtime; [ -n "$RENDER_API_KEY" ] && echo key set; gh auth status 2>&1 | head -2; env | grep -iE 'github|gh_|token' | sed 's/=.*/=<set>/'`
- `25s` `git ls-remote https://github.com/render-examples/express-hello-world 2>&1 | head -3; cd /home/runner/work/_temp/adb-mlvy1-realtime && git ls-files && git archive --format=tar.gz HEAD -- package.json p`
- `33s` `B=$(git archive --format=tar.gz HEAD -- package.json package-lock.json server.js store.js public | base64 -w0)`
- `38s` `for i in $(seq 1 50); do S=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-dbfrheec6qcc73emce4g/deploys/dep-dbfrhemc6qcc73emcfhg | jq -r .status); case $S i`
- `1m 12s` ❌ `curl -s https://adb-mlvy1-realtime-web.onrender.com/healthz; echo; node scripts/smoke.js https://adb-mlvy1-realtime-web.onrender.com; curl -s -o /dev/null -w "SSE %{http_code} %{content_type}\n" --max`
- `1m 33s` `cat > scripts/deploy.sh <<'EOF'`
