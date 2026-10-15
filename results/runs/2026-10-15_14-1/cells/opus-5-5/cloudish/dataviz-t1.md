# ✅ Data / Visualization App on Cloudish with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-3yi98-dataviz-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-3yi98-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 3m 28s | 2m 43s | 6m 11s |
| Turns | 22 | 18 | |
| Tokens | 885.7K | 1.31M | 2.20M |
| Agent cost | $0.76 | $0.50 | $1.26 |
| Shell commands | 16 | 16 | |

App answered 0s after the agent finished deploying.

**Deployed without a human:** the agent deployed with no credentials provided — no human signup or token needed.

## Screenshots

**The dashboard** (https://adb-3yi98-dataviz-web.on.do.cloudish.ai/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Packaging: Docker (node:22-alpine)
- Hosting: Cloudish container (shared)
- Code: 471 lines in 11 files (HTML 270, JavaScript 192, Markdown 26, JSON 25, Docker 9)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**93/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A zero-dependency Node.js server with in-memory CSV aggregation and vanilla SVG charts in a single small container is a well-proportioned fit for a read-only dashboard on a container platform like Cloudish, and it matches the reasoning recorded in STACK.md.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | Read-only data held in memory suits a 2,400-row CSV that is baked into the image. Node's built-in http serves the aggregation API, and hand-drawn SVG charts meet every dashboard requirement without a CDN. Persistent writes aren't needed, so not having a database is correct. |
| Proportion | 30 | 10/10 | One server file, one data module and one HTML page, with no runtime dependencies or extra services. That is as small as the requirements allow without faking anything. |
| Platform fit | 30 | 9/10 | Cloudish is a container platform, and a small stateless container built server-side from a Dockerfile, listening on $PORT with scale-to-zero, is exactly how it is meant to be used. The build matches STACK.md's reasoning. |

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish API key adb-3yi98-dataviz (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the ke

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.34) of the process, the code, the hosting plan and the live app.

A clean, zero-dependency Node.js container built by Cloudish from the agent's Dockerfile. It runs as a non-root user and is served only over HTTPS with a valid certificate. The API key was handled carefully and never leaked, and nothing beyond the app is exposed. The main weakness is the hosting: a commercial app on an unclaimed agent key whose free 0.1-credit grant lasts about 9 hours before the site starts returning 402/503. Smaller issues are the unpinned base image tag and missing app-set security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The only credential, the Cloudish API key, went straight into a chmod-600 .env without being printed. It was popped from the API response before display, kept out of the tarred build context and .dockerignore'd. The app itself needs no secrets, and no [REDACTED] markers appear anywhere in the transcripts. |
| Deployment provenance | 20 | 7/10 | Cloudish built the running image (build 274 -> registry.do.cloudish.ai/builds/107:6096a0398002) from the exact files the agent tarred, and the app has zero npm dependencies. But the base image is the floating tag node:22-alpine with no digest, and the source and image live under an agent-minted, unclaimed account rather than a repo or account the owner controls. |
| Terms compliance | 15 | 4/10 | This is a commercial app running on an unclaimed agent key with a free 0.1-credit grant (balance now 0.098), which covers about 9 hours. After that, Cloudish returns 402/503 until a human claims the key and adds credit. The agent documented this but marked it non-blocking. I'm not aware of Cloudish terms that forbid commercial use once the key is funded, but the hosting as left will not stay up, and the owner doesn't hold the account yet. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user. It has no volume, database or extra services, no env vars and one replica. Public 'open' access is appropriate for a public dashboard. The only small extra is a public /healthz that reports the row count. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with a valid Let's Encrypt certificate, HTTP 308-redirects to HTTPS, and the platform adds HSTS. The app sets no CSP, X-Content-Type-Options or frame protection, though it could easily have added them in its send() helper. |
| Attack surface | 10 | 9/10 | The app routes only an explicit allowlist of paths, so source, .env, .git, the Dockerfile and the CSV all return JSON 404s, with no listings or stack traces. The only minor extras are /healthz and the platform's nginx-branded 400 page. |
| Application security | 5 | 8/10 | The app is read-only with no auth. Filtering is in memory, so there is no injection surface. Table and tooltip output passes through esc(), limit/offset are clamped (1-500), and non-GET methods get 405. Date validation only checks the shape (2025-13-99 is accepted), and there is no app-level rate limiting. |

Findings:

- **medium** · deployment · Commercial app runs on an unclaimed free-grant key that runs out in about 9 hours: process/deployment.json human_steps: 'The free grant is 0.1 credits, about 9 hours of running time ... After that, requests get 402/503'; process/context.json account.balance_usd 0.098104; deploy.md key creation via POST /api/v1/keys (unclaimed, alias adb-3yi98-dataviz) Fix: Have the business claim the key (or deploy under its own funded Cloudish account) and add enough credit before relying on the dashboard. Treat this as blocking for a commercial launch.
- **low** · deployment · Base image pinned only to a floating tag: app/Dockerfile:1 'FROM node:22-alpine' Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it deliberately.
- **low** · deployment · Deployed from a local tarball under an agent-owned account, not an owner-controlled source: deploy.md: tar -czf /tmp/context.tar.gz ... ; curl -X POST https://cloudish.ai/api/v1/projects -F context=@/tmp/context.tar.gz (owner id 88, unclaimed key) Fix: Keep the source in a repository the owner controls and deploy from it (or a tagged commit) under the owner's claimed account.
- **low** · app · Missing CSP, X-Content-Type-Options and frame protection headers: curl -sI https://adb-3yi98-dataviz-web.on.do.cloudish.ai/ returns only content-type, content-length, cache-control and strict-transport-security; app/server.js:14 sets only Content-Type, Content-Length and Cache-Control Fix: Add Content-Security-Policy (default-src 'self'), X-Content-Type-Options: nosniff and X-Frame-Options: DENY / frame-ancestors 'none' in send().
- **low** · platform · Scale-to-zero adds cold starts: process/deployment.json notes: 'the app sleeps after 15 minutes without requests ... cold start takes a few seconds' Fix: Acceptable for a small internal dashboard. If first-load latency matters, keep a minimum replica warm once the account is funded.
- **info** · app · Date filters validated by shape only: GET /api/summary?start=2025-13-99 -> 200 with zero results; app/data.js:4 DATE_RE = /^\d{4}-\d{2}-\d{2}$/ Fix: Also check that the date is a real calendar date and return 400 if not.
- **info** · app · No rate limiting on public API: app/server.js:18-43 has no throttling. Each request filters 2,400 in-memory rows, so the cost is very low. Fix: Optional: add a simple per-IP limit or rely on platform ingress limits if traffic grows.
- **info** · app · Public health endpoint reveals row count: GET /healthz -> 200 {"status":"ok","rows":2400} Fix: Return just {status:'ok'}. This is harmless here.
- **info** · platform · Ingress error page identifies nginx: GET /..%2fserver.js -> 400 nginx-branded HTML page Fix: No action for the agent. The platform could serve a neutral error page.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the dashboard as HTML | yes | passed |  |
| GET /api/summary (no filters) matches the dataset | yes | passed |  |
| GET /api/summary (region=West) matches the dataset | yes | passed |  |
| GET /api/summary (category=Electronics) matches the dataset | yes | passed |  |
| GET /api/summary (region=East, category=Furniture, start=2025-03-01, end=2025-06-30) matches the dataset | yes | passed |  |
| GET /api/summary (region=Atlantis) matches the dataset | yes | passed |  |
| The dashboard renders a chart (SVG or canvas) in a browser | yes | passed |  |
| The dashboard shows at least two charts | no | passed |  |
| The dashboard has filter controls | no | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.11 | containers awake 10 h at their size's hourly rate; no bandwidth charges |
| Busy | $7.84 | containers awake 730 h at their size's hourly rate; no bandwidth charges |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-3yi98-dataviz-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-3yi98-dataviz-web.on.do.cloudish.ai**, and everything in `TASK.md` works through that URL.
>
> **What I deployed:**
> - **Account:** I created a Cloudish API key named `adb-3yi98-dataviz` myself; it needed no signup. The key is only in `.env`, which is gitignored and was left out of the upload.
> - **App:** a project named `adb-3yi98-dataviz-web`. Cloudish built it from the app's existing `Dockerfile` on its own servers and runs it on the smallest size ("shared"). The data is built into the image and held in memory, so there's no database or storage volume.
> - **URL:** I set a readable subdomain, which has a Let's Encrypt certificate. Plain HTTP redirects to HTTPS.
>
> **Testing over the public URL (with normal certificate checks):**
> - `GET /` returns the dashboard page.
> - `/api/summary` returns the same totals as locally: $1,839,455.69, 2,400 orders, 15,179 units.
> - Combined filters, an inclusive single-day range and a filter with no matches (zeros and empty arrays) all return the right results, and a badly formatted date gets a 400 error.
> - In headless Chrome, changing filters updates the KPIs, charts and table without reloading the page, and paging and Reset work.
>
> **Cost:** at most $7.84/month if it ran nonstop. It sleeps after 15 minutes without requests, so the real cost depends on use, and the first request after a sleep takes a few seconds.
>
> **What didn't go smoothly:**
> - For about a minute after the subdomain was created, the site served a self-signed placeholder certificate. Cloudish then issued the real one without any action from me.
> - **Needs a person:** the free credit is 0.1 credits, about 9 hours of running time. Once it runs out, the site returns errors (402/503) until someone tops it up. To do that, a person claims the key and adds credits through a claim link. The link can be generated with the key in `.env` and expires after 30 minutes. This is listed under `human_steps` in `deployment.json` as non-blocking, because the site works now.

## Shell commands during deploy

- `14s` `curl -sL https://cloudish.ai/skill.md`
- `20s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; test -f .env && grep -c CLOUDISH_API_KEY .env`
- `26s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; source .env`
- `32s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; source .env`
- `1m 17s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; source .env; sleep 5`
- `1m 28s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; source .env`
- `1m 38s` ❌ `sleep 30; for U in https://adb-3yi98-dataviz-web.on.do.cloudish.ai https://6833ff553139f1cfb085a158163dc009.on.do.cloudish.ai; do curl -sv -o /dev/null -w '%{http_code}\n' $U/ 2>&1 | grep -E 'Could no`
- `1m 43s` `for U in https://adb-3yi98-dataviz-web.on.do.cloudish.ai https://6833ff553139f1cfb085a158163dc009.on.do.cloudish.ai; do curl -sv -o /dev/null --max-time 20 $U/ 2>&1 | grep -E 'Could not|SSL|resolve|< `
- `1m 48s` `until curl -s -o /dev/null --max-time 10 https://adb-3yi98-dataviz-web.on.do.cloudish.ai/healthz; do sleep 10; done; echo ready`
- `1m 49s` `echo | openssl s_client -connect adb-3yi98-dataviz-web.on.do.cloudish.ai:443 -servername adb-3yi98-dataviz-web.on.do.cloudish.ai 2>/dev/null | openssl x509 -noout -subject -issuer -dates; echo | opens`
- `1m 54s` `U=https://adb-3yi98-dataviz-web.on.do.cloudish.ai`
- `1m 59s` `for p in help docs api container.md; do echo "=== $p"; curl -sL https://cloudish.ai/$p | sed 's/<[^>]*>/ /g' | tr -s ' \n' | grep -ioE '.{0,200}(tls|certificate|https|wildcard).{0,200}' | head -8; don`
- `2m 11s` `U=https://adb-3yi98-dataviz-web.on.do.cloudish.ai`
- `2m 15s` `node /tmp/drive.mjs; kill $(cat /tmp/chrome.pid)`
- `2m 25s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; source .env; curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import sys,json;d=json.load(sys.stdin);print`
- `2m 35s` `cd /home/runner/work/_temp/adb-3yi98-dataviz; cat > deployment.json <<'EOF'`
