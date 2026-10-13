# ✅ Data / Visualization App on Render with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-ysjix-dataviz-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-ysjix-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 56s | 2m 25s | 4m 21s |
| Turns | 15 | 11 | |
| Tokens | 508.5K | 622.1K | 1.13M |
| Agent cost | $0.44 | $0.30 | $0.74 |
| Shell commands | 10 | 9 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-ysjix-dataviz-web.onrender.com/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: `chart.js`, `express`
- Code: 337 lines in 11 files (JavaScript 240, HTML 91, JSON 35, Markdown 11, YAML 8, Shell 6)
- Dependencies: 2 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optional: push this repo to GitHub/GitLab and connect it to Render (or apply render.yaml as a Blueprint) so the service 

## Security and compliance review

**73/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.30) of the process, the code, the hosting plan and the live app.

The Render dashboard is live over HTTPS, exposes no files or secrets, and the app code is clean (validated dates, textContent rendering, clamped pagination). The main weaknesses are in how it was deployed and hosted. The code is an opaque base64 tarball uploaded as a Render secret file and run on a floating node:24-alpine tag; the container runs as root and reinstalls packages from npm on every start. It is also a commercial app on Render's free plan, which sleeps when idle, and the app sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The Render API key was only referenced as $RENDER_API_KEY and never printed. The env listing printed variable names only (`env \| cut -d= -f1`). The app needs no credentials, and no secrets show up in the source, the tarball or the live site. |
| Deployment provenance | 20 | 5/10 | Production runs an opaque base64 tarball uploaded from the agent's machine as a Render secret file, not a build from a repository the owner controls. The base image is a floating tag (node:24-alpine) with no digest, and dependencies are reinstalled from npm on every container start. The committed render.yaml does not describe what is actually deployed. |
| Terms compliance | 15 | 5/10 | This is a business (commercial) dashboard on Render's free web-service plan. Render presents that plan as being for hobby and testing use rather than production, and it spins down when idle, causing cold starts of 30-60 s. As far as I know Render does not explicitly forbid commercial use on the free plan, but it is a poor fit for a business app that should stay available. |
| Least privilege | 15 | 7/10 | There is a single public web service and no data stores, which is minimal. However, the container runs the stock node image as root, because the dockerCommand never switches to the image's built-in `node` user. |
| Transport security | 10 | 7/10 | HTTPS works with a valid certificate (behind Cloudflare), and HTTP returns a 301 redirect to HTTPS. The app sets none of HSTS, X-Content-Type-Options, frame protection or CSP, and it advertises X-Powered-By: Express. |
| Attack surface | 10 | 9/10 | Probes for .env, .git, package.json, server.js, data/sales.csv, node_modules, directory listings and path traversal all returned 404, and no stack traces leaked. The only minor item is the X-Powered-By banner along with Express's default error page. |
| Application security | 5 | 8/10 | Date parameters are validated, pagination is clamped (limit capped at 500), all rendering uses textContent (no XSS), and there is no database to inject into. There is no rate limiting on the public API, and array-style parameters are silently ignored instead of rejected. |

Findings:

- **medium** · deployment · App code delivered as an uploaded secret-file tarball, not built from an owner-controlled source: process/deploy.md:65 `tar czf /tmp/app.tgz app.js server.js ...`; deploy.md:78 creates the service with `"secretFiles":[{"name":"app.tgz.b64","content":b}]` and imagePath docker.io/library/node:24-alpine; start.sh runs `base64 -d /etc/secrets/app.tgz.b64 | tar xz`. The repo was never pushed (git status shows untracked files). app/render.yaml (runtime: node, npm ci/npm start) does not match the live service. Fix: Push the code to a Git repository the owner controls and deploy it through a Render Blueprint or native Node runtime (or a Dockerfile built from that repo), so production is traceable to a commit.
- **medium** · deployment · Unpinned base image and dependencies installed at runtime: deploy.md:78 imagePath `docker.io/library/node:24-alpine` (tag only, no @sha256 digest); app/deploy/start.sh line 5 runs `npm ci --omit=dev` on every container start, so each restart fetches packages from the npm registry. A package-lock.json is included in the tarball. Fix: Pin the base image by digest and install dependencies once at build time (a Dockerfile or the native build step), not on every start.
- **medium** · deployment · Commercial app hosted on Render free tier that sleeps when idle: process/context.json `use: commercial`; process/resources.json `plan: free`; deployment.json notes: 'Free-tier instances spin down when idle, so the first request after inactivity can take roughly 30-60 s.' Fix: Move the service to a paid Render instance type (for example Starter) intended for production, so it stays up and has support.
- **low** · deployment · Container runs as root: The service uses the stock node:24-alpine image (defaults to root) with dockerCommand `sh /etc/secrets/start.sh` (deploy.md:183). It extracts to /srv/app and runs node without dropping privileges. Fix: Run as the image's `node` user (a USER directive in a Dockerfile) and use a writable directory that user owns.
- **low** · app · Missing security headers: `curl -sI https://adb-ysjix-dataviz-web.onrender.com/` returns no strict-transport-security, x-content-type-options, x-frame-options/frame-ancestors or content-security-policy headers. app/app.js sets no headers. Fix: Add helmet (or set the headers manually) with HSTS, nosniff, frame-ancestors 'none' and a restrictive CSP. The inline script and style in index.html will need to be accounted for.
- **low** · app · X-Powered-By banner discloses framework: Response header `x-powered-by: Express` on GET /; unknown paths return Express's default 'Cannot GET /...' page. Fix: Call app.disable('x-powered-by') and add a custom 404 handler.
- **low** · app · No rate limiting on public API: app/app.js: /api/summary and /api/orders (up to 500 rows per request) have no rate limiting or caching. Fix: Add a lightweight rate limiter (for example express-rate-limit) or rely on a CDN or WAF rule.
- **info** · app · Array-style query parameters are silently ignored: GET /api/summary?region[]=a returned 200 with all 2400 orders (app/app.js parseQuery accepts only strings). Fix: Return 400 for non-string filter values so callers know their filter wasn't applied.
- **info** · deployment · API key handled only through environment variable: deploy.md:4 lists env names only (`env | cut -d= -f1`); every API call uses `Authorization: Bearer $RENDER_API_KEY`. No [REDACTED] values appear in any output. Fix: None required. Note that the secret-file feature was used to carry code, not credentials.

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
| service | adb-ysjix-dataviz-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-ysjix-dataviz-web.onrender.com** and every requirement in `TASK.md` works through that URL.
>
> **What's deployed:** one free Render web service, `adb-ysjix-dataviz-web` (`srv-db7brq2j9qps73brhrb0`) in the Oregon region. It costs $0 a month and is the only resource I created.
>
> **An unusual setup:** there were no GitHub credentials, so I couldn't connect a repository for Render to build from. Instead:
> - The service runs Node's official public image, `node:24-alpine`.
> - The app code and `sales.csv` (about 47 KB packed) are stored on the service as a Render "secret file".
> - A second secret file, a start script, unpacks the code, installs dependencies and starts the server. A copy is in `deploy/start.sh`.
>
> To ship a change, re-upload the packed code through Render's API and trigger a new deploy. Pushing the repo to GitHub and connecting it to Render would allow normal builds and auto-deploy on push. That needs a person, so I listed it in `deployment.json` as an optional step; nothing is blocked without it. The secret files contain no credentials, and I didn't create any, so there's no `.env`.
>
> **What I tested through the public URL:**
> - **API:** with no filters it returns $1,839,455.69 in revenue, 2,400 orders and 15,179 units. East + Software in March returns $20,333.64, 14 orders and 140 units. A region that doesn't exist returns zeros and empty arrays, and a badly formatted date gets a `400`.
> - **Dashboard:** in a scripted browser, setting the region, category and date filters updated the KPI tiles, both charts and the order table without reloading the page.
>
> **What didn't work:** my first deploy failed because Render didn't read the quoted start command the way I expected. Putting the commands in the start script fixed it.
>
> **Limitation:** on the free plan the service goes to sleep when idle, so the first request after a quiet period can take about 30–60 seconds.
>
> `deployment.json` is written, and I committed everything to the local git repo.

## Shell commands during deploy

- `4s` `env | cut -d= -f1 | grep -iE "git|render|token" ; git status --short | head; git remote -v; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/owners | head -c 600; echo; cur`
- `16s` `tar czf /tmp/app.tgz app.js server.js package.json package-lock.json public data && ls -l /tmp/app.tgz && base64 -w0 /tmp/app.tgz | wc -c; which render; npm view @render/cli 2>/dev/null | head -2`
- `25s` `python3 - <<'EOF' > /tmp/create.json`
- `30s` `for i in $(seq 1 40); do s=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-db7brq2j9qps73brhrb0/deploys/dep-db7brqaj9qps73brhs50 | python3 -c "import json,s`
- `48s` `curl -s -H "Authorization: Bearer $RENDER_API_KEY" "https://api.render.com/v1/logs?ownerId=tea-db6fig0473hc73eb9aeg&resource=srv-db7brq2j9qps73brhrb0&limit=50&direction=backward" | python3 -c "`
- `58s` `S=srv-db7brq2j9qps73brhrb0; H="Authorization: Bearer $RENDER_API_KEY"`
- `1m 49s` `U=https://adb-ysjix-dataviz-web.onrender.com`
- `2m 01s` `mkdir -p /tmp/pw && cd /tmp/pw && npm i playwright@1 >/dev/null 2>&1 && cat > t.js <<'EOF'`
- `2m 17s` `mkdir -p deploy && cp /tmp/start.sh deploy/start.sh && printf '.env\n' >> .gitignore && cat > deployment.json <<'EOF'`
