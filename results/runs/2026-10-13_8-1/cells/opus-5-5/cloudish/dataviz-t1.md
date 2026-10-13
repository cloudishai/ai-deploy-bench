# ✅ Data / Visualization App on Cloudish with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-mq202-dataviz-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-mq202-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 57s | 2m 26s | 5m 23s |
| Turns | 15 | 14 | |
| Tokens | 591.9K | 934.0K | 1.53M |
| Agent cost | $0.57 | $0.36 | $0.94 |
| Shell commands | 10 | 13 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-mq202-dataviz-web.on.do.cloudish.ai/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: —
- Code: 492 lines in 12 files (JavaScript 369, CSS 64, HTML 49, JSON 24, Docker 10, Markdown 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-mq202-dataviz' (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the key 

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.34) of the process, the code, the hosting plan and the live app.

The agent built a small, dependency-free Node dashboard that runs as non-root, handles its one credential carefully, serves only allowlisted files over valid HTTPS with HSTS, and validates its inputs. The main weakness is fit for purpose: a business's app runs on an unclaimed $0.10 free credit grant that the agent says will fail with 402/503 after about 9 hours, yet it marked funding as non-blocking. Smaller issues are an unpinned base image, no source repository, missing app-level security headers, and permissive CORS added by the platform.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to a chmod-600 .env without being printed, kept out of git and the uploaded build context, and the app itself needs no secrets. No credential appears in source, logs or the live site. |
| Deployment provenance | 20 | 7/10 | The live image is the one Cloudish built server-side from the agent's own uploaded context, and the app has no third-party dependencies. The base image is a floating tag (node:22-alpine) with no digest, and the source exists only as a local tarball upload under an unclaimed key, not in a repository the owner controls. |
| Terms compliance | 15 | 4/10 | This is a business's dashboard, but it runs on an unclaimed key with a $0.10 free grant that the agent itself estimates lasts about 9 hours before requests fail with 402/503. The agent marked claiming and funding the key as non-blocking. I don't know of any Cloudish term that forbids commercial use on pay-as-you-go credits, but no account holder has accepted terms or set up billing, so the app can't stay up as deployed. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user, with no data store, volume or env secrets. Public access is what the dashboard needs. The only issue is that the platform's ingress reflects any Origin with credentials allowed and advertises write methods. |
| Transport security | 10 | 8/10 | HTTPS only: HTTP gets a 308 redirect to HTTPS, the Let's Encrypt certificate is valid, and the platform adds HSTS. The app could have set X-Content-Type-Options, frame protection and a CSP in its own Node server and didn't. |
| Attack surface | 10 | 9/10 | The server answers only from an explicit allowlist of static files and API routes. Source files, .env, .git, the Dockerfile and the CSV all return 404, and error responses are short JSON with no stack traces. The only extras are a harmless /healthz and the platform's permissive CORS preflight. |
| Application security | 5 | 8/10 | Dates are checked against a regex, region and category are exact-match comparisons against in-memory data so there's no injection path, the page size is capped at 500, and the frontend writes data with textContent rather than innerHTML. The public API has no rate limiting, and the company's order data is public with no authentication, though the task didn't ask for any. |

Findings:

- **medium** · deployment · Business app runs on an unclaimed free credit grant that runs out in hours: process/deployment.json: plan "unclaimed key, free 0.1 credit grant"; human_steps says the grant "covers about 9 hours of running time ... After that, requests return 402/503" but marks it "blocking": false. process/context.json: use "commercial", balance_usd 0.098981. Fix: Have the business claim the key under its own Cloudish account, accept the terms and add billing before go-live. Treat this as a blocking step, not an optional one.
- **low** · deployment · Scale-to-zero gives a cold start on the first request after idle: process/deployment.json notes: "the default idle timeout scales it to zero when there's no traffic ... After idling, the first request has a cold start"; process/deploy.md shows the app returning 000 at first while it started. Fix: If the dashboard needs to respond quickly at all times, raise the idle timeout or keep one replica always on once billing is in place.
- **low** · deployment · Base image not pinned to a digest: app/Dockerfile line 1: FROM node:22-alpine Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it on purpose.
- **low** · deployment · Deployed from a local tarball, with no source repository the owner controls: process/deploy.md: tar ... -czf /tmp/context.tar.gz . then POST /api/v1/projects -F context=@/tmp/context.tar.gz; the agent's git status returned "fatal: not a git repository" Fix: Commit the source to a repository the owner controls and build from a tagged commit, so the deployed image can be traced back to reviewed code.
- **low** · platform · Ingress reflects any Origin with credentials allowed: curl -H 'Origin: https://evil.example' /api/summary -> access-control-allow-origin: https://evil.example, access-control-allow-credentials: true; OPTIONS preflight -> access-control-allow-methods: GET,HEAD,PUT,PATCH,POST,DELETE. app/src/server.js sets no CORS headers. Fix: The platform should leave CORS to the app or default to same-origin. Impact here is low because the app has no cookies or auth and only answers GET/HEAD (POST returns 405).
- **low** · app · Missing X-Content-Type-Options, frame protection and CSP: curl -sI https://adb-mq202-dataviz-web.on.do.cloudish.ai/ returns only content-type, vary, CORS headers and strict-transport-security; app/src/server.js lines 21-22 and 45 set only Content-Type and Cache-Control. Fix: Set X-Content-Type-Options: nosniff, Content-Security-Policy (default-src 'self'; frame-ancestors 'none') and Referrer-Policy in the Node server's responses.
- **low** · app · No rate limiting on public API endpoints: app/src/server.js lines 33-41: /api/summary and /api/orders filter and sort all rows on every request with no throttling; GET /api/orders?limit=999999 -> 200 with limit capped at 500. Fix: Add simple per-IP rate limiting or caching of summary results. The dataset is small, so the risk is mainly cost from unbounded scale-up, not outage.
- **info** · app · Company order data is public with no authentication: GET /api/orders -> 200 {"total":2400,...} with no credentials; access "open" in process/resources.json Fix: The task didn't require auth, but if the sales data is internal, put the dashboard behind authentication or the platform's access controls.
- **info** · deployment · API key handled without exposure: process/deploy.md: key written via jq to .env with chmod 600 and never echoed; tar --exclude='.env*' context listing shows no .env; .dockerignore and .gitignore list .env; docker env {}  Fix: No change needed. Rotate the key once it is claimed if the build host is shared.

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
| project | adb-mq202-dataviz-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The sales dashboard is live at **https://adb-mq202-dataviz-web.on.do.cloudish.ai**, and everything in `TASK.md` works through that URL. The one thing it needs from a person is more credits soon (see below).
>
> **What I deployed**
> - I created a Cloudish API key named `adb-mq202-dataviz` and saved it only in `.env`, which is excluded from git and from the uploaded build.
> - The project `adb-mq202-dataviz-web` was built on Cloudish from my Dockerfile. It runs one container on the cheapest size (`shared`) and shuts down when idle.
> - I swapped the random URL for the readable subdomain above. Cloudish handles the HTTPS certificate; it was self-signed for about the first 20 seconds, then worked.
>
> **What I tested through the public URL**
> - The dashboard page and its files all return 200.
> - `/api/summary` with no filters returns 2,400 orders, 15,179 units and $1,839,455.69, with 12 months and categories sorted by revenue. That matches the local results.
> - Combining all four filters (region, category, start and end date) gives the right result, and a filter that matches nothing returns zeros and empty arrays.
> - A malformed date returns 400, and the orders table pages through results.
> - In a headless browser, changing the filters updated the KPIs, both charts and the table without a page reload, with no errors.
>
> **Cost and the step that needs a person**
> - If it ran all the time, it would cost about $7.84/month. Because it shuts down when idle, the real cost is lower, but the first request after a quiet spell is slower.
> - The free grant was $0.10 and about $0.099 is left, which covers roughly 9 more hours of running time. After that the app returns 402/503 errors. To keep it up, someone has to claim the key and add credits; I listed this as a non-blocking step under `human_steps` in `deployment.json`.
>
> Nothing failed.

## Shell commands during deploy

- `2s` `curl -s https://cloudish.ai/skill.md`
- `5s` `cd /home/runner/work/_temp/adb-mq202-dataviz; ls -a; grep -q CLOUDISH_API_KEY .env 2>/dev/null && echo has-key; curl -s https://cloudish.ai/instances.md | head -40`
- `10s` `cd /home/runner/work/_temp/adb-mq202-dataviz; echo .env >> .gitignore; echo .env >> .dockerignore`
- `14s` `cd /home/runner/work/_temp/adb-mq202-dataviz; source .env`
- `18s` `cd /home/runner/work/_temp/adb-mq202-dataviz; source .env`
- `1m 20s` `cd /home/runner/work/_temp/adb-mq202-dataviz; source .env`
- `1m 23s` `cd /home/runner/work/_temp/adb-mq202-dataviz; source .env`
- `1m 28s` `U=https://adb-mq202-dataviz-web.on.do.cloudish.ai; sleep 5`
- `1m 37s` ❌ `curl -sv https://adb-mq202-dataviz-web.on.do.cloudish.ai/healthz 2>&1 | tail -8; dig +short adb-mq202-dataviz-web.on.do.cloudish.ai; curl -s -o /dev/null -w "%{http_code}\n" https://d14499a3105fec6307`
- `1m 43s` `for i in $(seq 1 30); do a=$(curl -s -o /dev/null -w "%{http_code}" https://adb-mq202-dataviz-web.on.do.cloudish.ai/healthz); b=$(curl -s -o /dev/null -w "%{http_code}" https://d14499a3105fec630791b16`
- `1m 59s` `U=https://adb-mq202-dataviz-web.on.do.cloudish.ai`
- `2m 08s` `cd /home/runner/work/_temp/adb-mq202-dataviz; source .env; curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq '{alias: (.apiKey.alias // .alias), balance: (.apiKey`
- `2m 18s` `cd /home/runner/work/_temp/adb-mq202-dataviz; cat > deployment.json <<'EOF'`
