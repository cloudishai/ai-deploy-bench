# ✅ Data / Visualization App on Render with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-j6usb-dataviz-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-j6usb-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 16s | 2m 21s | 4m 38s |
| Turns | 15 | 15 | |
| Tokens | 582.8K | 921.8K | 1.50M |
| Agent cost | $0.53 | $0.40 | $0.93 |
| Shell commands | 11 | 12 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-j6usb-dataviz-web.onrender.com/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: `express`
- Code: 439 lines in 11 files (JavaScript 320, CSS 62, HTML 57, JSON 34, Markdown 13, YAML 8)
- Dependencies: 1 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optionally push this project to a GitHub/GitLab repo and connect it to Render (or point the service at it / use render.y

## Security and compliance review

**74/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.32) of the process, the code, the hosting plan and the live app.

The sales dashboard is a small, read-only Express app with clean input handling. No secrets leaked and nothing beyond the app is exposed: HTTPS is enforced, and source, .env and .git paths return 404. The main weaknesses are in how it was deployed: the code was shipped as a base64 tarball in a Render secret file on a floating node:24-alpine tag, with npm ci at every start and the container running as root. The business app also sits on Render's free plan, which sleeps when idle and isn't meant for production; security headers and rate limiting are missing too.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Render API key was only ever used as $RENDER_API_KEY in curl headers and never printed. The app needs no secrets, and the bundle, transcripts and live site show no credentials. |
| Deployment provenance | 20 | 5/10 | The running code is the bundle the agent built, but it was shipped as a base64 tarball in a Render 'secret file', not from a version-controlled repo. It runs on the floating node:24-alpine tag, and npm ci pulls dependencies from the public registry on every container start. |
| Terms compliance | 15 | 5/10 | A business's dashboard (use=commercial) is hosted on Render's free web-service plan. To my knowledge Render doesn't explicitly forbid commercial use on that plan, but it markets free instances for testing and hobby work, not production. They also spin down after about 15 minutes idle, causing 30-60 s cold starts that the agent itself acknowledged. |
| Least privilege | 15 | 7/10 | There is only one public web service and no data stores or extra resources. However, the container runs the stock node image as root, and the start script never drops to the built-in 'node' user. |
| Transport security | 10 | 8/10 | HTTPS works with a valid certificate, and HTTP gets a 301 redirect to HTTPS. Responses carry no HSTS, X-Content-Type-Options, frame-protection or CSP headers, which the Express app could easily have set. |
| Attack surface | 10 | 9/10 | Only the public/ directory is served statically. Source files, package files, .env, .git, the CSV and the secret files all return 404, and error responses contain no stack traces. The only extras are a benign /healthz and /api/meta. |
| Application security | 5 | 8/10 | Date parameters are validated (400 on a bad format), non-string query values are ignored, page size is capped at 500, and table cells are rendered with textContent. There is no rate limiting on the public API, and the tooltip uses innerHTML (with trusted CSV data only). |

Findings:

- **medium** · deployment · Commercial app on Render free plan that sleeps when idle: process/context.json use=commercial; process/resources.json plan=free; deployment.json notes: 'The free plan sleeps after ~15 minutes idle, so the first request after that takes roughly 30-60 s' Fix: Use a paid Render instance type (e.g. Starter) for a business's dashboard so it stays up and runs under production-grade terms.
- **medium** · deployment · Application code delivered as a 'secret file' rather than from a tracked source: process/deploy.md: tar czf /tmp/bundle/app.tgz ... ; create.json secretFiles [{name:'app.tgz.b64', content: b64}]; start.sh runs 'base64 -d /etc/secrets/app.tgz.b64 | tar xz' Fix: Deploy from a Git repo the owner controls, or from a built and pushed image referenced by digest, so each deploy is traceable to a commit or artifact.
- **medium** · deployment · Unpinned base image and dependency install at every runtime start: process/deploy.md: imagePath 'docker.io/library/node:24-alpine' (tag, no digest); start.sh: 'npm ci --omit=dev --no-audit --no-fund' runs on each container start; app/package.json: "express": "^5.3.0" Fix: Pin the base image by digest and install dependencies at build time into an immutable image (the lockfile pins versions, but each restart still depends on the npm registry and a moving base tag).
- **low** · deployment · Container runs as root: process/deploy.md: dockerCommand 'sh /etc/secrets/start.sh' on stock node:24-alpine (default user root); start.sh does mkdir /srv/app and exec node app.js with no user switch Fix: Build an image with 'USER node' (or run the process as the node user) and keep app files read-only.
- **low** · app · No security headers (HSTS, CSP, X-Content-Type-Options, frame protection): curl -sI https://adb-j6usb-dataviz-web.onrender.com/ returns only content-type, cache-control, etag, server: cloudflare, x-render-origin-server; app/app.js sets no headers beyond disabling x-powered-by Fix: Add helmet (or set the headers manually) with HSTS, a strict CSP (the app uses only same-origin scripts and styles), nosniff and frame-ancestors 'none'.
- **low** · app · No rate limiting on public API endpoints: app/app.js:33-45 /api/summary and /api/orders (limit up to 500 rows per request) have no throttling Fix: Add a lightweight rate limiter (e.g. express-rate-limit) or rely on a CDN or WAF rule.
- **info** · app · Tooltip HTML built with innerHTML from API data: app/public/app.js:17 showTip sets tip.innerHTML; lines 78 and 107 interpolate month and category names from the read-only CSV Fix: Build tooltip content with textContent and DOM nodes, so future data sources can't inject markup.
- **info** · app · Default Express error pages; nothing sensitive exposed: GET /.env, /.git/config, /package.json, /data.js, /data/sales.csv, /render.yaml all return 404 'Cannot GET ...'; GET /api/summary?start=bad returns 400 JSON error with no stack trace Fix: Optionally add a custom 404/error handler; no action required.

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
| Light use | $0.00 | fixed monthly prices; 0.04 GB out of the Hobby workspace's 5 GB; free instances awake 10 h of 750 free hours |
| Busy | $7.13 | fixed monthly prices; 52.6 GB out of the Hobby workspace's 5 GB, 47.6 GB billed (with a payment method on file; without one Render suspends the services instead); free instances awake 730 h of 750 free hours |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| service | adb-j6usb-dataviz-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The sales dashboard is live at **https://adb-j6usb-dataviz-web.onrender.com** on Render's free plan, so it costs $0 a month. I tested every `TASK.md` requirement through that URL and they all work.
>
> **What I checked on the live site:**
> - **Dashboard:** `/` loads, and a browser screenshot with filters applied showed the KPIs, both charts and the orders table updating to match.
> - **`/api/summary`:** with no filters it returns all 2,400 orders and $1,839,455.69. With all four filters combined, the result exactly matches the same calculation run locally. A filter that matches nothing returns zeros and empty arrays.
>
> **How it's deployed:** there were no GitHub or other Git credentials, so I couldn't deploy from a repository the normal way.
> - I created one web service, `adb-j6usb-dataviz-web` (id `srv-db7eqru7bikc73akg0og`), that runs the public Node.js image (`node:24-alpine`).
> - The app code is packed into a small archive (about 65 KB, no secrets) and stored as a Render "secret file". A second secret file, `start.sh`, unpacks it, installs dependencies and starts the server.
>
> **What didn't work at first:**
> - The API rejected my first service request because I used the wrong field name for the image.
> - The first deploy then failed because Render didn't run the quoted startup command as written. Putting the startup steps in `start.sh` fixed it.
>
> **Limitations:**
> - **Updating the code:** you have to re-upload the archive through the Render API and start a new deploy. Pushing a commit won't redeploy anything.
> - **Cold starts:** the free plan sleeps after about 15 minutes without traffic. The first request after that takes around 30–60 seconds.
>
> **`deployment.json`:** it's written. Its one `human_steps` entry is optional, not blocking: push the project to GitHub or GitLab and connect it to Render, to get normal builds and auto-deploys. I didn't create any credentials, so there's nothing in `.env`. I added `.env` to `.gitignore`.
>
> Sources:
> - [Deploy without GitHub/GitLab – Render feature request](https://feedback.render.com/features/p/deploy-without-githubgitlab)
> - [Deploying on Render – Render Docs](https://render.com/docs/deploys)
> - [render-oss/skills render-deploy SKILL.md](https://github.com/render-oss/skills/blob/main/skills/render-deploy/SKILL.md)

## Shell commands during deploy

- `5s` `cd /home/runner/work/_temp/adb-j6usb-dataviz; env | cut -d= -f1 | grep -iE 'git|render|token' ; git status --short | head; git remote -v; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api`
- `28s` `cd /home/runner/work/_temp/adb-j6usb-dataviz; rm -rf /tmp/bundle && mkdir /tmp/bundle; npm ci --omit=dev >/dev/null 2>&1; tar czf /tmp/bundle/app.tgz app.js data.js package.json package-lock.json data`
- `32s` `cd /home/runner/work/_temp/adb-j6usb-dataviz; tar czf /tmp/bundle/app.tgz app.js data.js package.json package-lock.json data public; base64 -w0 /tmp/bundle/app.tgz > /tmp/bundle/app.tgz.b64; ls -la /t`
- `39s` `cd /tmp/bundle; python3 - <<'EOF' > /tmp/bundle/create.json`
- `43s` ❌ `cd /tmp/bundle; for img in "docker.io/library/node:24-alpine" "node:24-alpine"; do sed -i "s#\"imageUrl\": \"[^\"]*\"#\"imageUrl\": \"$img\"#" create.json; grep -o '"imageUrl": "[^"]*"' create.json; c`
- `48s` `cd /tmp/bundle; sed -i 's#"imageUrl": "[^"]*"#"imagePath": "docker.io/library/node:24-alpine"#' create.json; curl -s -X POST -H "Authorization: Bearer $RENDER_API_KEY" -H "Content-Type: application/js`
- `53s` `for i in $(seq 1 40); do s=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-db7eqru7bikc73akg0og/deploys/dep-db7eqs67bikc73akg1j0 | python3 -c "import json,s`
- `1m 11s` `curl -s -H "Authorization: Bearer $RENDER_API_KEY" "https://api.render.com/v1/logs?ownerId=tea-db6fig0473hc73eb9aeg&resource=srv-db7eqru7bikc73akg0og&limit=40&direction=backward" | python3 -c "import `
- `1m 20s` `cat > /tmp/bundle/start.sh <<'EOF'`
- `1m 57s` `U=https://adb-j6usb-dataviz-web.onrender.com`
- `2m 01s` `cd /tmp; chromium --headless --no-sandbox --disable-gpu --window-size=1280,900 --virtual-time-budget=5000 --screenshot=/tmp/live.png 'https://adb-j6usb-dataviz-web.onrender.com/?category=Furniture&sta`
- `2m 13s` `cd /home/runner/work/_temp/adb-j6usb-dataviz; printf 'node_modules\n.env\n' > .gitignore`
