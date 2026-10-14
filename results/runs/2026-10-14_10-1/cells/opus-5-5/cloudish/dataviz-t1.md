# ✅ Data / Visualization App on Cloudish with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-sno8g-dataviz-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-sno8g-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 54s | 2m 59s | 4m 52s |
| Turns | 7 | 13 | |
| Tokens | 239.5K | 733.1K | 972.5K |
| Agent cost | $0.36 | $0.35 | $0.71 |
| Shell commands | 5 | 12 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-sno8g-dataviz-web.on.do.cloudish.ai/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Packaging: Docker (node:22-alpine)
- Hosting: Cloudish container (shared)
- Code: 364 lines in 10 files (HTML 186, JavaScript 168, JSON 24, Docker 10, Markdown 10)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-sno8g-dataviz' into a human account and add credits (mint a fresh link with GET https://clou

## Security and compliance review

**76/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.49) of the process, the code, the hosting plan and the live app.

The sales dashboard is a small Node app with no dependencies, built and deployed carefully: the Cloudish key never left a gitignored .env or entered the build context, the container runs as non-root, only the app's routes are exposed, and HTTPS has a valid certificate, an HTTP redirect and HSTS. The main weaknesses concern fit, not code: a commercial app runs on an anonymous, unclaimed key with a roughly 9-hour free credit grant that will take it offline, and the default 'open' access makes the company's order-level sales data public. Smaller issues are an unpinned base image, missing app-level security headers and no rate limiting.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The only credential, the Cloudish API key, was written straight to a gitignored .env without being printed, was excluded from the uploaded build context, and the app needs no runtime secrets. One small gap: .dockerignore does not list .env, so the exclusion relied entirely on the tar command. |
| Deployment provenance | 20 | 7/10 | The image was built server-side from a tarball of the reviewed source, and the running image tag matches the build. The app has no dependencies. The base image node:22-alpine is a floating tag with no digest pin, and the source is an ad-hoc local upload rather than a versioned repository. |
| Terms compliance | 15 | 5/10 | A business app runs on an unclaimed, anonymous API key that only has the free 0.1-credit grant (balance $0.0988, about 9 hours of uptime), with no human or business account behind it. The app will start returning 402/503 once the grant runs out, and the agent marked claiming the key as non-blocking. I found no published Cloudish terms that rule out commercial use (cloudish.ai/terms returns only an API stub), so I'm not sure what the plan terms are. |
| Least privilege | 15 | 7/10 | The container runs as the non-root node user, there is no data store or volume, and only the app port is exposed. The project uses the default 'open' access mode, so the company's full order-level sales data is readable by anyone without credentials, and every request is billed to the owner. Cloudish offers a private mode that was not considered. |
| Transport security | 10 | 8/10 | The site is HTTPS only, HTTP gets a 308 redirect to HTTPS, it has a valid Let's Encrypt certificate, and the platform sets HSTS. The app sets no X-Content-Type-Options, frame protection or CSP even though its own server writes every response header. The old random hostname still serves the app behind a self-signed certificate. |
| Attack surface | 10 | 9/10 | The app serves only an explicit route whitelist. Requests for .env, .git, source files, the CSV, Dockerfile, /admin and /debug all return a JSON 404, and no stack traces leak. The platform's nginx error page and the old random hostname, which still answers, are minor leftovers. |
| Application security | 5 | 8/10 | Dates are checked against a regex, filters use exact in-memory matching (there is no injection surface), page_size and page are clamped, the frontend escapes all data before using innerHTML, and methods other than GET/HEAD get 405. There is no rate limiting on the unauthenticated, owner-billed API, and the app sets no CSP as defense in depth. |

Findings:

- **medium** · deployment · Commercial app hosted on an unclaimed free-grant key that will run out: process/deployment.json resources[0].plan: 'unclaimed key, free 0.1-credit grant'; human_steps: 'about 9 hours of container uptime ... requests return 402/503 until credits are added', marked "blocking": false; process/context.json use=commercial, balance_usd=0.098817 Fix: Before treating this as production, have the business claim the key into its own Cloudish account, accept the provider's terms there and fund it. Mark this human step as blocking for a commercial launch.
- **medium** · deployment · Company sales data publicly readable with 'open' access: process/deploy.md project create response: "access": "open"; process/resources.json details.access=open; GET https://adb-sno8g-dataviz-web.on.do.cloudish.ai/api/orders?page_size=99999 -> 200 with 200 order rows (12 pages covering all 2400 orders), no credential required Fix: If the dashboard is for internal use, switch the project to private access or add authentication (for example, an OIDC login in front of the app) so only company staff can read order-level data and wake the billed container.
- **low** · deployment · Base image not pinned by digest: app/Dockerfile line 1: FROM node:22-alpine Fix: Pin the base image to a specific version and digest (node:22.x-alpine@sha256:...) and update it on purpose.
- **low** · deployment · Deployed from an ad-hoc local tarball rather than versioned source: process/deploy.md: tar --exclude='.env*' ... -czf /tmp/context.tar.gz . && curl ... -F context=@/tmp/context.tar.gz Fix: Commit the source to a repository the owner controls and build from a tagged commit so the deployed image can be traced back to a reviewed revision.
- **low** · app · Missing security headers the app could set: curl -sI https://adb-sno8g-dataviz-web.on.do.cloudish.ai/ -> only content-type, cache-control, strict-transport-security (no X-Content-Type-Options, X-Frame-Options/frame-ancestors, Content-Security-Policy); app/server.js line 16 writeHead sets only Content-Type and Cache-Control Fix: Add X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none' (or X-Frame-Options: DENY) and Referrer-Policy in the send() helper.
- **low** · platform · Old random hostname still serves the app with a self-signed certificate: curl https://7e96939ce544109a4eb39c71029d87c1.on.do.cloudish.ai/healthz -> 'SSL certificate problem: self-signed certificate'; with -k -> 200 Fix: The platform should tear down or redirect the replaced hostname with a valid certificate. The agent could have confirmed the old label was removed.
- **low** · app · No rate limiting on unauthenticated, owner-billed endpoints: app/server.js lines 33-66: no throttling; skill.md: 'an open ... project also answers with no credential at all, billed to its owner' Fix: Add simple per-IP rate limiting or restrict access so outside traffic cannot keep the container awake and drain credits.
- **info** · deployment · .dockerignore does not exclude .env: app/.dockerignore lists node_modules, .git, test, *.md only; .env was kept out only by tar --exclude='.env*' in process/deploy.md Fix: Add .env and .env* to .dockerignore as defense in depth for future builds that use a different upload method.
- **info** · platform · Platform nginx error page reveals the server software: GET /%2e%2e/server.js -> 400 HTML page '<center>nginx</center>' Fix: Platform could serve generic error pages. No action needed from the app.

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
| project | adb-sno8g-dataviz-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-sno8g-dataviz-web.on.do.cloudish.ai** with a valid HTTPS certificate, and every requirement in `TASK.md` works through that URL.
>
> **What I deployed**
> - **API key:** I created a Cloudish API key named `adb-sno8g-dataviz`; it came with 0.1 free credits. The key is saved only in `.env`, which is in `.gitignore` and was left out of the uploaded files.
> - **App:** a project named `adb-sno8g-dataviz-web`, built on Cloudish from the step-1 Dockerfile. It runs on the cheapest size, `shared`, and shuts down after 15 minutes without traffic.
> - **Address:** I replaced the random address Cloudish assigned with the readable one above. It took about 30 seconds after the change before the certificate was issued and the URL answered.
> - **Cost:** about $0.011 per hour while the app is running. Running non-stop would cost about $7.84 a month; with the automatic shutdown it costs only what it's used. The 0.1 credits left after setup cover about 9 hours of running time.
>
> **Checks through the public URL**
> - The dashboard page returns 200 and renders in headless Chrome. With region and category filters set, the tiles showed 171 orders, $240,117.98 and 1,823 units, matching the API, and the charts and paginated table were filled in.
> - With no filters, `/api/summary` returns 2,400 orders, $1,839,455.69 and 15,179 units. A separate count of the CSV gives the same numbers.
> - Filters combine correctly, and start and end dates both count. Months come back in ascending order and categories by revenue, highest first.
> - A filter that matches nothing returns 200 with zeros and empty lists.
>
> **Needs a person (doesn't block anything now):** once the free credits run out, the app stops answering until someone adds more. That requires a person to claim the key into a Cloudish account and add credits. A claim link can be created with the key in `.env`; each link expires after 30 minutes. This is listed under `human_steps` in `deployment.json`.
>
> Nothing failed. The first request after the app has been idle takes a few seconds while it starts up.

## Shell commands during deploy

- `7s` `curl -sL https://cloudish.ai/skill.md; echo ----; curl -sL https://cloudish.ai/instances.md`
- `13s` `ls -a; test -f .env && grep -c CLOUDISH_API_KEY .env`
- `18s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude='node_modules' -czf /tmp/context.tar.gz . && tar -tzf /tmp/context.tar.gz | head -30 && curl -s -X POST https://cloudis`
- `22s` `set -a && . ./.env && set +a && for i in $(seq 40); do R=$(curl -s https://cloudish.ai/api/v1/images/builds/255 -H "Authorization: Bearer $CLOUDISH_API_KEY"); S=$(echo "$R"|jq -r .build.status); [ "$S`
- `1m 36s` `set -a && . ./.env && set +a && sleep 5; curl -s https://cloudish.ai/api/v1/projects/adb-sno8g-dataviz/adb-sno8g-dataviz-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq 'del(.project.owner)'`
- `1m 44s` `set -a && . ./.env && set +a && curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-sno8g-dataviz/adb-sno8g-dataviz-web/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: appl`
- `1m 48s` `U=https://adb-sno8g-dataviz-web.on.do.cloudish.ai; sleep 3`
- `1m 55s` ❌ `dig +short adb-sno8g-dataviz-web.on.do.cloudish.ai; curl -sv https://adb-sno8g-dataviz-web.on.do.cloudish.ai/healthz 2>&1 | tail -5; curl -s -w ' %{http_code}\n' https://7e96939ce544109a4eb39c71029d87`
- `1m 59s` `for i in $(seq 30); do c=$(curl -s -o /dev/null -w '%{http_code}' https://adb-sno8g-dataviz-web.on.do.cloudish.ai/healthz); echo "$i $c"; [ "$c" = 200 ] && break; sleep 10; done; curl -sv https://adb-`
- `2m 23s` `U=https://adb-sno8g-dataviz-web.on.do.cloudish.ai`
- `2m 30s` `python3 -I -c "`
- `2m 51s` `set -a && . ./.env && set +a && curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq -c '.runway // .'| head -c 400; echo`
