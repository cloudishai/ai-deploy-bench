# ✅ Data / Visualization App on Cloudish with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-a08uf-dataviz-web.cloudish.app (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $0.33)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-a08uf-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 00s | 1m 41s | 3m 41s |
| Turns | 13 | 13 | |
| Tokens | 497.8K | 894.5K | 1.39M |
| Agent cost | $0.53 | $0.39 | $0.91 |
| Shell commands | 9 | 10 | |

App answered 0s after the agent finished deploying.

**Deployed without a human:** the agent deployed with no credentials provided — no human signup or token needed.

## Screenshots

**The dashboard** (https://adb-a08uf-dataviz-web.cloudish.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 24
- Frameworks: Node.js http module (built in)
- Packaging: Docker (node:24-alpine)
- Hosting: Cloudish container (shared)
- Code: 416 lines in 10 files (HTML 231, JavaScript 176, Markdown 38, JSON 25, Docker 9)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

### Stack fit

**93/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Node.js 24 with only built-in modules, data held in memory and vanilla JS/SVG is a minimal, well-reasoned stack for a read-only dashboard, and the build followed STACK.md exactly. It suits Cloudish's sleep-when-idle containers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | Holding a read-only 2,400-row CSV in memory with a small Node HTTP server and hand-drawn SVG charts covers every requirement. Summing in integer cents keeps revenue totals exact. |
| Proportion | 30 | 10/10 | There is one file with no dependencies, no database and no front-end framework, which is as small as the requirements allow without faking anything. |
| Platform fit | 30 | 9/10 | A single small stateless container that sleeps after 15 idle minutes matches Cloudish's container model and billing well. The only cost is a 2–3 s wake-up on the first request after sleeping. |

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Open a claim link (mint one with GET https://cloudish.ai/api/v1/credits/claim using the key in .env), sign in to Cloudis

## Security and compliance review

**84/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.33) of the process, the code, the hosting plan and the live app.

This zero-dependency Node.js dashboard is cleanly built and deployed on Cloudish. The API key never left a chmod-600 .env, the container runs as a non-root user, the server answers only on an explicit route allowlist, and the app is served only over HTTPS with HSTS. The main weakness is hosting: this commercial app runs on a 0.1-credit free grant that lasts about 9 awake hours, and the agent marked topping up as non-blocking. Smaller issues are an unpinned base image and missing app-level security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The only credential, the Cloudish API key, was written straight to a chmod-600 .env, never echoed, and kept out of the build context by both the tar excludes and .dockerignore. The app itself needs no secrets. |
| Deployment provenance | 20 | 8/10 | The image was built on the server from the agent's own Dockerfile and a local source tarball, and the running container uses that build (builds/206:033e728b3c1d). There are no third-party dependencies, but the base image is the floating tag node:24-alpine with no digest pin. |
| Terms compliance | 15 | 5/10 | This is a commercial app running on a 0.1-credit free grant that covers only about 9 awake hours, after which it returns 402/503. The agent marked topping up as non-blocking. I don't know of any Cloudish term that forbids commercial use on prepaid credits, and sleeping when idle is fine for a dashboard, but the hosting will not keep the app up as funded. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user, on the smallest shared size, with no volume, no data store and no extra services. Public 'open' access is needed for the dashboard, though it does publish the company's order-level sales data to anyone. |
| Transport security | 10 | 8/10 | HTTPS works with a managed certificate, HTTP returns a 308 redirect to HTTPS, and the platform sends HSTS. The app sets no X-Content-Type-Options, frame protection or CSP, though it easily could. |
| Attack surface | 10 | 10/10 | The server answers only on an explicit route allowlist. Requests for .env, .git, source files, the CSV, path traversal and admin paths all return a JSON 404, and nothing leaks stack traces or debug information. |
| Application security | 5 | 9/10 | The app is read-only. Filters are compared by exact match, date formats are checked, limit and offset are clamped, other methods get a 405, and the client escapes data before inserting it as HTML. Two minor gaps: impossible dates such as 2025-02-30 are accepted, and there is no rate limiting, though each request is cheap. |

Findings:

- **medium** · deployment · Commercial app funded only by a free grant that runs out in about 9 hours: process/deployment.json: plan 'free grant (0.1 credits)', human_steps says 'about 9 hours of awake time ... Once it runs out, the app returns 402/503', marked "blocking": false; process/context.json use=commercial, balance_usd 0.099605 Fix: Treat adding credits (or a funded billing setup) as a blocking step before handing over a business app, and consider wakeEveryMinutes or alwaysOn if the app must stay responsive.
- **low** · deployment · Base image not pinned to a digest: app/Dockerfile:1 `FROM node:24-alpine` Fix: Pin the base image by digest (node:24-alpine@sha256:...) and update it on purpose.
- **low** · app · Missing security headers (nosniff, frame protection, CSP): curl -D - https://adb-a08uf-dataviz-web.cloudish.app/ returns only content-type, cache-control and strict-transport-security (HSTS added by the platform); app/server.js:93 sets only Content-Type and Cache-Control Fix: Have send() add X-Content-Type-Options: nosniff, X-Frame-Options: DENY (or frame-ancestors 'none') and a restrictive Content-Security-Policy.
- **low** · deployment · Company order-level sales data is publicly readable: process/resources.json access 'open'; GET /api/orders?limit=1 returns full order rows without authentication Fix: If the data is not meant to be public, put the app behind Cloudish's sign-in (OIDC) or restrict project access.
- **info** · app · Impossible calendar dates accepted as filters: GET /api/summary?start=2025-02-30 -> 200 with filtered results; app/server.js:44 relies on regex + lenient Date.parse Fix: Round-trip the parsed date (new Date(v).toISOString().slice(0,10) === v) and reject mismatches with 400.
- **info** · app · No rate limiting on public API: app/server.js:102-127 has no throttling; each request is an in-memory scan of 2,400 rows Fix: Acceptable at this scale; add light per-IP throttling if the API is ever expensive or metered.

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
| project | adb-a08uf-dataviz-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-a08uf-dataviz-web.cloudish.app**, and everything in `TASK.md` works through that public URL.
>
> **What I checked on the live site:**
> - **Dashboard:** a headless-browser screenshot with the Software category and an April–September date range showed the filters, KPI tiles, both charts and the paginated orders table all updating correctly.
> - **`/api/summary`:**
>   - With no filters it covers all 2,400 rows ($1,839,455.69).
>   - With region, category and dates combined, the totals match an independent Python calculation (9 orders, $12,712.26).
>   - When nothing matches it returns zeros and empty arrays.
>   - A malformed date returns `400`.
>
> **What I set up:**
> - **API key `adb-a08uf-dataviz`:** created through Cloudish's no-signup API. The key is saved in `.env`, which is left out of the upload to Cloudish.
> - **Container app `adb-a08uf-dataviz-web`:** Cloudish built it from the `Dockerfile` on their servers. It runs on the cheapest size (`shared`) with Cloudish's HTTPS certificate on the `*.cloudish.app` domain.
>
> **Cost:** the app sleeps after 15 minutes without requests and is only charged while awake, at about $0.011 an hour. That's roughly $0.33 a month at about an hour of use a day; keeping it on all the time would be $7.84 a month. The first request after it has been asleep takes about 2–3 seconds.
>
> **Limitation:** the account only has Cloudish's free 0.1 credits, which covers about 9 hours of awake time. After that the site stops responding until someone adds credits. I listed that in `human_steps` in `deployment.json` as non-blocking: a person opens a claim link, signs in to Cloudish and adds credits. A fresh link comes from `GET https://cloudish.ai/api/v1/credits/claim` with the key in `.env`, and each link expires after 30 minutes.

## Shell commands during deploy

- `18s` `mkdir -p /tmp/cld && curl -sL https://cloudish.ai/skill.md -o /tmp/cld/skill.md; curl -sL https://cloudish.ai/instances.md -o /tmp/cld/inst.md; wc -l /tmp/cld/*; cat /tmp/cld/inst.md`
- `22s` `cat /tmp/cld/skill.md`
- `27s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; resp=$(curl -s -X POST https://cloudish.ai/api/v1/keys -H "content-type: application/json" -d '{"alias":"adb-a08uf-dataviz","agent":"claude-code","model":`
- `31s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; set -a; . ./.env; set +a; printf '.env*\n' >> .gitignore; printf '.env*\ndeployment.json\n' >> .dockerignore`
- `35s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; set -a; . ./.env; set +a; for i in $(seq 1 60); do s=$(curl -s https://cloudish.ai/api/v1/images/builds/593 -H "Authorization: Bearer $CLOUDISH_API_KEY");`
- `50s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; set -a; . ./.env; set +a; curl -s -X PUT https://cloudish.ai/api/v1/projects/$CLOUDISH_ALIAS/adb-a08uf-dataviz-web/subdomain -H "Authorization: Bearer $CL`
- `54s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; set -a; . ./.env; set +a; curl -s https://cloudish.ai/api/v1/projects/$CLOUDISH_ALIAS/adb-a08uf-dataviz-web -H "Authorization: Bearer $CLOUDISH_API_KEY" |`
- `59s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; U=https://adb-a08uf-dataviz-web.cloudish.app; curl -s -m 90 -o /dev/null -w 'root %{http_code} %{time_total}s\n' $U/; curl -s $U/ | grep -o '<title>.*</ti`
- `1m 08s` `cd /tmp; timeout 40 chromium --headless --no-sandbox --disable-gpu --window-size=1280,900 --virtual-time-budget=5000 --screenshot=/tmp/pub.png 'https://adb-a08uf-dataviz-web.cloudish.app/?category=Sof`
- `1m 33s` `cd /home/runner/work/_temp/adb-a08uf-dataviz; set -a; . ./.env; set +a; curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import sys,json; d=json.load(sy`
