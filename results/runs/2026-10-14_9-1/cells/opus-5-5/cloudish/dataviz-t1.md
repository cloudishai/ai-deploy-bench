# ✅ Data / Visualization App on Cloudish with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-t3ndz-dataviz-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: Light use: $0.11/month, Busy: $7.84/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-t3ndz-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 54s | 2m 14s | 4m 07s |
| Turns | 10 | 15 | |
| Tokens | 352.3K | 838.4K | 1.19M |
| Agent cost | $0.37 | $0.38 | $0.75 |
| Shell commands | 8 | 13 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-t3ndz-dataviz-web.on.do.cloudish.ai/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: —
- Code: 345 lines in 9 files (HTML 181, JavaScript 154, JSON 21, Docker 10)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-t3ndz-dataviz' (mint a link with GET https://cloudish.ai/api/v1/credits/claim using the key 

## Security and compliance review

**78/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.39) of the process, the code, the hosting plan and the live app.

The dashboard is a small, dependency-free Node app. It handles its secrets cleanly, runs as non-root, is served over valid HTTPS with a redirect and HSTS, and exposes nothing beyond its own endpoints. The main problem is hosting fit: a business's commercial app sits on an unclaimed, free 0.1-credit key that stops serving after about 9 running hours, and the agent marked the fix as non-blocking. Smaller issues are a base image pinned only by tag, missing app-set security headers, a possible crash from a malformed URL, and a default platform hostname that serves the app with a fake certificate.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Cloudish API key was written straight to a chmod-600 .env, never echoed (only alias/balance printed), excluded from .gitignore, .dockerignore and the uploaded tarball. The app itself needs no secrets. |
| Deployment provenance | 20 | 7/10 | The image was built server-side from a tarball of the agent's own local sources and deployed by immutable tag, and the app has no npm dependencies. But the base image node:22-alpine is pinned only by a mutable tag, and the account is an unclaimed agent-minted key, so the business does not yet control the deployment. |
| Terms compliance | 15 | 3/10 | A business's commercial dashboard runs on an unclaimed, free 0.1-credit key that covers about 9.3 running hours, after which the app stops serving. Claiming the key and adding credits is listed as non-blocking when for a business app it is required. I'm not sure what Cloudish's terms say about commercial use on free grants. |
| Least privilege | 15 | 9/10 | The container runs as the non-root node user, there is no data store or volume, and open access fits a public dashboard. The only extra public entry point is the platform's default random hostname, which still serves the app. |
| Transport security | 10 | 8/10 | The custom subdomain has a valid Let's Encrypt certificate, HTTP gets a 308 redirect to HTTPS and HSTS is set. The app sets no CSP, X-Content-Type-Options or frame protection, and the default hostname serves the app with the ingress's fake certificate. |
| Attack surface | 10 | 9/10 | Probes for .env, .git, the source files, Dockerfile, the raw CSV, admin and debug paths all returned the app's JSON 404. Errors are generic. Only an nginx 400 page reveals the proxy software. |
| Application security | 5 | 7/10 | Dates are validated, filters are exact in-memory matches with no injection surface, the client escapes data before inserting it into innerHTML, and page size is capped at 500. But a malformed request target can make new URL() throw outside any try/catch, which can crash the process, and there is no rate limiting. |

Findings:

- **high** · deployment · Commercial app hosted on an unclaimed free-credit key that runs out after ~9 hours: process/context.json: use=commercial, balance_usd 0.099499. deploy.md project-create response: runway runningHoursLeft 9.3, 'Apps on this key stop serving at a zero balance'. process/deployment.json human_steps: claim the key and add credits, marked "blocking": false. Fix: Have the business claim the key (or deploy under a business-owned, funded Cloudish account) and add credits before treating the dashboard as live. For an app that must stay up, mark this step as blocking.
- **medium** · deployment · Deployment owned by an agent-minted, unclaimed key: deploy.md: POST https://cloudish.ai/api/v1/keys with no auth created owner 'adb-t3ndz-dataviz' (id 77). deployment.json: plan 'unclaimed key'. Fix: Transfer ownership to the business by claiming the key, and keep the source in a repository the owner controls.
- **medium** · app · Malformed request URL can crash the server (uncaught exception): app/server.js:36 `new URL(req.url, 'http://localhost')` runs in the request handler with no try/catch. Locally, new URL('//[', 'http://localhost') throws ERR_INVALID_URL, and an uncaught throw in a Node 'request' listener ends the process. Not tested against the live app, to avoid disrupting it. Fix: Wrap URL parsing in try/catch and return 400, or add a top-level try/catch in the handler.
- **low** · deployment · Base image pinned by tag, not digest: app/Dockerfile:1 `FROM node:22-alpine` Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it on purpose.
- **low** · app · No rate limiting on public API endpoints: app/server.js:44-60: /api/summary and /api/orders (up to 500 rows per request) are unauthenticated and unthrottled. Credits are billed per running hour, so steady traffic keeps the instance awake and drains the balance. Fix: Add basic per-IP rate limiting or response caching for the summary results.
- **low** · app · Missing security headers the app could set: curl -sI https://adb-t3ndz-dataviz-web.on.do.cloudish.ai/ returns only content-type, cache-control and strict-transport-security: no Content-Security-Policy, X-Content-Type-Options or X-Frame-Options/frame-ancestors. server.js:14 sets only Content-Type and Cache-Control. Fix: Set CSP (e.g. default-src 'self' with the inline script hashed), X-Content-Type-Options: nosniff and frame-ancestors 'none' in send().
- **low** · platform · Default random hostname serves the app with an invalid certificate: https://ce731e346ac96c0921bb6b2051c84966.on.do.cloudish.ai/healthz: curl fails certificate verification (exit 60). The certificate is 'Kubernetes Ingress Controller Fake Certificate'. With -k it returns 200. Fix: The platform should issue valid certificates for default hostnames or retire them once a custom label is set. The agent could check whether the default hostname can be disabled.
- **low** · platform · Extra public entry point via default hostname: The default ce731e....on.do.cloudish.ai hostname still routes to the app (200 with -k) after the custom subdomain was assigned (deploy.md PUT .../subdomain). Fix: Disable the unused default hostname if the platform allows it.
- **info** · platform · Proxy error page reveals nginx: GET /%2e%2e/server.js returns 400 with an nginx HTML error page. All other probes (/.env, /.git/config, /server.js, /package.json, /Dockerfile, /data/sales.csv, /admin, /debug) returned the app's JSON 404. Fix: No action needed. The platform could use a generic error page.
- **info** · deployment · API key handled correctly: deploy.md: key saved via `echo CLOUDISH_API_KEY=... > .env; chmod 600 .env`. tar ran with --exclude='.env*', and app/.dockerignore lists .env*. No secrets appear in the transcripts or the app source. Fix: None.

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
| project | adb-t3ndz-dataviz-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-t3ndz-dataviz-web.on.do.cloudish.ai**, and every requirement in `TASK.md` works through that URL.
>
> **What I set up:**
> - **API key `adb-t3ndz-dataviz`:** I created it myself through Cloudish's API, which needs no sign-up. It came with the free 0.1-credit grant and is saved only in `.env`. That file is in `.gitignore` and was left out of the uploaded build files.
> - **Project `adb-t3ndz-dataviz-web`:** Cloudish built the container from my Dockerfile on its own servers. It runs on the smallest size (`shared`) and sleeps when idle, so it only costs credits while it's awake. I swapped the random web address Cloudish gave it for a readable one. Cost so far is $0 because it runs on the free credits.
>
> **Checked through the public URL:**
> - **Dashboard (`GET /`):** I loaded it in a headless Chrome browser. With no filters the KPIs read $1,839,455.69 in revenue, 2,400 orders and 15,179 units. Setting region, category and dates (West, Furniture, June) updated the KPIs, both charts and the orders table without reloading the page, and the browser reported no errors.
> - **Summary API (`GET /api/summary`):** For 5 filter combinations its answers exactly match totals I calculated directly from the CSV. A filter that matches nothing returns zeros and empty arrays.
>
> **Limits:**
> - **Credits run out:** the free credits cover about 9.3 hours of the app being awake. When they're used up, the app stops responding until someone adds more.
> - **Wake-up delay:** the first request after a quiet spell takes a few seconds while the app wakes up.
>
> **For a person to do (not blocking):** to keep the app running long-term, someone needs to claim the key and add credits. It's listed under `human_steps` in `deployment.json`, which says how to create the claim link (it expires 30 minutes after it's created).

## Shell commands during deploy

- `3s` `curl -sL https://cloudish.ai/skill.md`
- `8s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; ls -a; grep -q CLOUDISH_API_KEY .env 2>/dev/null && echo HAVE || {`
- `12s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; source .env`
- `16s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; source .env`
- `45s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; source .env`
- `50s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; source .env`
- `54s` `U=https://adb-t3ndz-dataviz-web.on.do.cloudish.ai`
- `58s` ❌ `sleep 20; curl -sv https://adb-t3ndz-dataviz-web.on.do.cloudish.ai/healthz 2>&1 | tail -8; curl -s -o /dev/null -w "%{http_code}\n" https://ce731e346ac96c0921bb6b2051c84966.on.do.cloudish.ai/healthz`
- `1m 23s` `U=https://adb-t3ndz-dataviz-web.on.do.cloudish.ai`
- `1m 32s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; python3 - <<'EOF'`
- `1m 43s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i -s playwright@1 >/dev/null 2>&1 && npx playwright install --with-deps chromium >/dev/null 2>&1; cat > t.js <<'EOF'`
- `1m 56s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; source .env; curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | jq -c '{runway, settings: .settings, idle: .apiKey.setti`
- `2m 06s` `cd /home/runner/work/_temp/adb-t3ndz-dataviz; cat > deployment.json <<'EOF'`
