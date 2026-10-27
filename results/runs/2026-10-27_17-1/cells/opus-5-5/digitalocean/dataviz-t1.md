# ✅ Data / Visualization App on DigitalOcean with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-kb60n-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 11s | 2m 08s | 5m 12s |
| Turns | 16 | 8 | |
| Tokens | 645.9K | 448.4K | 1.39M |
| Agent cost | $0.59 | $0.19 | $0.93 |
| Shell commands | 12 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 53s, 292.9K tokens, $0.16).

## Screenshots

**The dashboard** (https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 20
- Frameworks: Node.js http module (built in)
- Packaging: Docker (node:20-alpine), App spec (.do/app.yaml)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 540 lines in 12 files (JavaScript 391, HTML 118, JSON 24, Shell 22, Markdown 16, YAML 16, Docker 9)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Zero-dependency Node.js with in-memory data and vanilla SVG is a well-proportioned fit for a read-only 2,400-row dashboard and API. The one departure from STACK.md is that it is delivered as a locally built image through DOCR, not built from source on App Platform.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | The read-only CSV is held in memory, which suits 2,400 rows, and revenue is summed in integer cents for exact rounding. Hand-drawn SVG charts with fetch-based filter updates meet every dashboard requirement. |
| Proportion | 30 | 10/10 | There is one server.js on Node's built-in http module, with zero npm dependencies, no build step and no database. That is about as simple as the requirements allow, and it is still correct. |
| Platform fit | 30 | 8/10 | A single App Platform web service with a health check fits a small API plus dashboard. However, the agent built the Docker image locally and pushed it to DOCR, rather than letting App Platform build from source as STACK.md described. That adds a registry and a manual build path. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**89/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.28) of the process, the code, the hosting plan and the live app.

A small, dependency-free Node.js dashboard on a paid DigitalOcean App Platform Basic service, which fits commercial use. Secrets were handled cleanly, the container runs as non-root, and probes found nothing exposed beyond the app. The main weaknesses are provenance (a local build pushed with a mutable :latest tag on an unpinned base image) and missing security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no runtime secrets. The DigitalOcean token was kept in a git- and docker-ignored .env, read by deploy.sh, and filtered out of the deploy output. The Dockerfile copies only named files, and no credential appears in the source or transcripts. |
| Deployment provenance | 20 | 6/10 | The image was built from the agent's local working directory and pushed to the owner's private DOCR, with no source repository or CI involved. The base image (node:20-alpine) and the deployed image tag (latest) are mutable and not pinned by digest. There are no third-party dependencies, which reduces supply-chain risk. |
| Terms compliance | 15 | 10/10 | This commercial app runs on a paid App Platform Basic service, which always stays up and allows commercial use, plus the free DOCR starter tier, which DigitalOcean permits for commercial use. Nothing relies on a tier that sleeps or expires. |
| Least privilege | 15 | 10/10 | The container runs as the non-root node user. There is no database, the registry is private, and the app consists of a single public web service with no extra components. |
| Transport security | 10 | 8/10 | The app is served over HTTPS with the platform certificate, and HTTP redirects to HTTPS with a 301. No security headers (HSTS, X-Content-Type-Options, frame protection, CSP) are sent, and the app's own handler could easily have set them. |
| Attack surface | 10 | 10/10 | Static files are served only from public/, with a path-traversal guard. Probes for .env, .git, server.js, Dockerfile, the CSV and traversal paths all return 404 JSON. Errors are generic, with no stack traces. |
| Application security | 5 | 8/10 | Dates are strictly validated, other filters are only compared for exact equality, non-GET methods are rejected and the orders limit is capped at 500. Table rendering uses textContent, but tooltips use innerHTML with CSV values (trusted data). The app has no rate limiting of its own beyond the platform's Cloudflare front end. |

Findings:

- **low** · deployment · Unpinned base image and mutable :latest deploy tag: app/Dockerfile:1 `FROM node:20-alpine`; app/.do/app.yaml image `tag: latest`; deploy.sh builds and pushes `...:latest` Fix: Pin the base image by digest. Tag images with a commit SHA or digest and reference that tag in the app spec.
- **low** · deployment · Deployed from a local build, not from version-controlled source: process/deploy.md: `./deploy.sh` runs `docker build` in the agent's working directory and pushes to DOCR. No git repo or CI is involved. Fix: Deploy from a git repository the owner controls, for example with App Platform's GitHub source or a CI pipeline that builds tagged commits.
- **low** · app · No security headers: curl -sI https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app/ returns only content-type, cache-control and Cloudflare headers, with no HSTS, X-Content-Type-Options, X-Frame-Options or CSP. server.js:110-124 sets only Content-Type and Cache-Control. Fix: Set Strict-Transport-Security, X-Content-Type-Options: nosniff, frame-ancestors/X-Frame-Options and a restrictive CSP in sendJson and serveStatic.
- **info** · app · Tooltip uses innerHTML with data values: app/public/app.js:37 `tip.innerHTML = html`, called at lines 79 and 109 with d.month and d.category from the CSV Fix: Build the tooltip with textContent and DOM elements, so changes to the data source can't inject markup.
- **info** · app · No application-level rate limiting: server.js:127-146 has no throttling. Each request scans all 2,400 rows, which is cheap, and the Cloudflare front end (server: cloudflare) absorbs basic abuse. Fix: Optional: add simple per-IP rate limiting or caching of summary results if traffic grows.

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
| Light use | $5.00 | fixed monthly prices; 0.0373 GiB out of a 50 GiB allowance |
| Busy | $5.00 | fixed monthly prices; 49 GiB out of a 50 GiB allowance |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| app | adb-kb60n-dataviz | adb-kb60n-dataviz-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-kb60n-dataviz-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-kb60n-dataviz | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app**, and every requirement in `TASK.md` works through that URL.
>
> **What's running:**
> - **App Platform app `adb-kb60n-dataviz`:** one web service, `adb-kb60n-dataviz-web`, on the Basic `apps-s-1vcpu-0.5gb` plan at $5/month. It runs the Docker image and gets HTTPS automatically on the `ondigitalocean.app` address. It's the cheapest option that can run a server; the free tier only hosts static files, which can't serve `/api/summary`.
> - **Container registry `adb-kb60n-dataviz`:** the free starter tier, holding the image in a repository named `adb-kb60n-dataviz-web`.
> - **Total:** about $5/month.
>
> **What I tested on the public URL:**
> - **`/api/summary`:** for six filter combinations it returned exactly the numbers I computed locally from the CSV. These were no filters, one filter, all filters combined, a single-day range, and queries that match nothing (zeros and empty arrays).
> - **Bad date:** a malformed date returns 400.
> - **The dashboard:** I opened `/` in headless Chrome with a category and start date in the URL. The filters, KPI tiles, both charts and the latest-50 orders table all showed the filtered results.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty. I didn't create any new credentials; the deploy used the token from your environment. To redeploy after changes, run `./deploy.sh`.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-kb60n-dataviz; doctl account get --format Email,Status,DropletLimit 2>&1 | tail -1; doctl registry get 2>&1 | tail -2; doctl apps list --format ID,Spec.Name 2>&1`
- `9s` `cd /home/runner/work/_temp/adb-kb60n-dataviz; ./deploy.sh 2>&1 | grep -v -iE 'token' | tail -25`
- `1m 42s` `cd /home/runner/work/_temp/adb-kb60n-dataviz; U=https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app`
- `1m 48s` `cd /tmp; google-chrome --headless=new --no-sandbox --disable-gpu --window-size=1280,900 --virtual-time-budget=5000 --screenshot=/tmp/live.png 'https://adb-kb60n-dataviz-cdqxy.ondigitalocean.app/?categ`
- `1m 50s` `cd /home/runner/work/_temp/adb-kb60n-dataviz; doctl registry get --format Name,StorageUsageBytes --no-header; doctl apps get 6a3e3ed1-6b8c-4ab4-b368-87615aee94d0 --format ActiveDeployment.Phase --no-h`
- `2m 02s` `cd /home/runner/work/_temp/adb-kb60n-dataviz; cat > deployment.json <<'EOF'`
