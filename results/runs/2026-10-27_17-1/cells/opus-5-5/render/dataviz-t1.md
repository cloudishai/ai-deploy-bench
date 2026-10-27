# ✅ Data / Visualization App on Render with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-lt4yb-dataviz-web.onrender.com (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $7.13/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-lt4yb-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 15s | 4m 35s | 7m 39s |
| Turns | 14 | 13 | |
| Tokens | 544.4K | 843.1K | 1.62M |
| Agent cost | $0.54 | $0.33 | $1.04 |
| Shell commands | 9 | 12 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 48s, 231.0K tokens, $0.17).

## Screenshots

**The dashboard** (https://adb-lt4yb-dataviz-web.onrender.com/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Packaging: Render Blueprint (render.yaml)
- Hosting: Render web service (free, running the prebuilt image node:22-alpine)
- Code: 478 lines in 12 files (HTML 247, JavaScript 182, Shell 49, Markdown 28, JSON 21, YAML 13)
- Dependencies: 0 npm, 0 Python
- Deploy config: `render.yaml`

### Stack fit

**81/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A zero-dependency Node server with in-memory data and a vanilla SVG front end fits this small read-only dashboard well and is well proportioned. The Render delivery, a stock image plus secret files on the free tier, departs from the planned git-based native runtime and fits the platform less well.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | A read-only 2,400-row CSV kept in memory, with aggregation per request in Node's built-in http module, fully meets the spec. The vanilla JS/SVG front end updates without reloads, and summing in integer cents handles the rounding. |
| Proportion | 30 | 9/10 | There are zero dependencies, no build step and no database, which is as simple as the requirements allow. STACK.md explains rejecting pandas and Postgres. The unused render.yaml is a little extra clutter. |
| Platform fit | 30 | 6/10 | A single Render web service suits this app, and STACK.md planned a native Node runtime deploy from git. The build departed from that: it runs a stock image and loads code from secret files, which works against Render's git/native-runtime flow. The free instance's sleep also hurts a business dashboard. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**69/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.35) of the process, the code, the hosting plan and the live app.

The app is a small, dependency-free Node server with sound input validation, output escaping and no exposed files or secrets, served over HTTPS with an HTTP-to-HTTPS redirect. The main weaknesses are in the deployment. The code was uploaded as Render secret files onto a floating-tag node:22-alpine image running as root, so there is no repo-backed or pinned provenance. A business's dashboard is on Render's free plan, which sleeps when idle, and the app sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The Render API key was only read from the environment ($RENDER_API_KEY) and is redacted in every transcript command. The app needs no secrets, and .gitignore excludes .env. The only oddity is that Render's secret-files feature was used to ship ordinary app code, which is a misuse but leaks nothing. |
| Deployment provenance | 20 | 5/10 | Production runs app files that were uploaded straight from the agent's working tree as Render secret files, on top of the floating tag docker.io/library/node:22-alpine. There is no repo-backed build, no commit link and no pinned image digest, and the committed render.yaml describes a different, git-based deploy. Having zero npm dependencies helps a lot. |
| Terms compliance | 15 | 4/10 | This is a business's app running on a free Render web service. Render positions free instances for hobby and testing use, not production, and they spin down after 15 minutes idle, so a cold start takes 30-60 s. I'm not sure Render's terms outright forbid commercial use, but the plan doesn't fit a business dashboard that should stay available. |
| Least privilege | 15 | 7/10 | There is a single public web service and no data stores or extra resources. However, the stock node:22-alpine image runs as root by default, and the docker command `node /etc/secrets/server.js` doesn't switch to the image's built-in `node` user. |
| Transport security | 10 | 7/10 | HTTPS works with a valid certificate through Render/Cloudflare, and HTTP returns 301 to HTTPS. The app sets no HSTS, CSP, X-Content-Type-Options or frame-protection headers, although its own send() function could easily have added them. |
| Attack surface | 10 | 9/10 | Requests for /.env, /.git/config, /server.js, /package.json, /data/sales.csv, /render.yaml and a path-traversal path all return a JSON 404. Errors are generic, with no stack traces. The extra /api/meta, /api/orders and /healthz endpoints reveal only dashboard data and a row count. |
| Application security | 5 | 8/10 | Dates are checked against a regex and Date.parse, other methods get 405, the orders limit is capped at 500, and CSV-derived values are HTML-escaped before innerHTML. There is no rate limiting on public endpoints and no access control on company sales data, but the spec didn't ask for auth. |

Findings:

- **medium** · deployment · Commercial dashboard on Render free plan that sleeps: process/context.json use=commercial; process/resources.json plan=free; process/deployment.json notes: 'sleeps after 15 minutes idle and the first request after that takes about 30-60 seconds' Fix: Move the service to a paid instance type (e.g. Starter) so it stays up and is used under production-appropriate terms.
- **medium** · deployment · App code deployed as Render secret files instead of from a source repo: process/deploy.md: POST /v1/services with "secretFiles":[{name:'server.js'...},{'lib.js'},{'index.html'},{'sales.csv'}] read from the local working tree and "dockerCommand":"node /etc/secrets/server.js" Fix: Push the repo to a Git host the owner controls and deploy from it (the committed render.yaml already describes this), or build and push a versioned image, so every deploy maps to a commit.
- **low** · deployment · Base image referenced by floating tag: process/deploy.md: "imagePath":"docker.io/library/node:22-alpine"; process/resources.json source=docker.io/library/node:22-alpine Fix: Pin the image by digest (node:22-alpine@sha256:...) or use Render's native Node runtime with a pinned NODE_VERSION.
- **low** · deployment · Committed render.yaml does not describe what is deployed: app/render.yaml: runtime: node, buildCommand npm install, autoDeploy: true; the live service is runtime=image with secret files (process/resources.json) Fix: Keep infrastructure-as-code in sync with the live service, or remove the unused blueprint.
- **low** · deployment · Container process runs as root: process/deploy.md: stock node:22-alpine image (default user root) with dockerCommand 'node /etc/secrets/server.js'; no USER set Fix: Run as the image's unprivileged 'node' user, e.g. through a small Dockerfile with USER node, or use Render's native runtime.
- **low** · app · No security headers: curl -D - https://adb-lt4yb-dataviz-web.onrender.com/ shows only content-type, cache-control and Render/Cloudflare headers; no strict-transport-security, content-security-policy, x-content-type-options or x-frame-options. app/server.js:19 sets only Content-Type and Cache-Control Fix: Add HSTS, X-Content-Type-Options: nosniff, frame-ancestors/X-Frame-Options and a CSP in send().
- **low** · app · No rate limiting or access control on company sales data: GET /api/orders?limit=99999 -> 200 with up to 500 order rows; no auth anywhere in app/server.js:23-50 Fix: If the data is confidential, put the dashboard behind authentication. Add basic per-IP rate limiting.
- **info** · deployment · Secret-file mechanism used for non-secret code: process/deploy.md secretFiles payload contains server.js, lib.js, index.html, sales.csv Fix: Reserve secret files for credentials; deliver code through a repo or image.
- **info** · app · Extra endpoints beyond spec: GET /healthz -> {"status":"ok","rows":2400}; GET /api/meta and /api/orders return filter metadata and order rows Fix: Acceptable for a dashboard. Make sure the health endpoint reveals nothing sensitive.

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
| service | adb-lt4yb-dataviz-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The sales dashboard is live at **https://adb-lt4yb-dataviz-web.onrender.com**, and every requirement in `TASK.md` passed when I tested it through that URL. Nothing needed a person, so `human_steps` is empty.
>
> **What's deployed:** one Render web service, `adb-lt4yb-dataviz-web` (id `srv-dbfrd3ijnfac738kivq0`), on the free plan, so the cost is $0 a month.
>
> **How it runs:** there were no GitHub credentials, so Render had no git repo to build from. Instead the service runs the public official Node image, `docker.io/library/node:22-alpine`. The app's four files (`server.js`, `lib.js`, `index.html`, `sales.csv`) are uploaded to Render as secret files, and the service starts with `node /etc/secrets/server.js`. To support this I made one small change: `server.js` now reads the page's file path from an environment variable (`INDEX_FILE`). The local tests still pass, and the change is committed.
>
> **Testing on the public URL:**
> - **Smoke test:** `scripts/smoke.sh` passed. It checks the dashboard page, the unfiltered and combined-filter summaries, the response when nothing matches, and the orders endpoint. A malformed date returns 400.
> - **Browser check:** choosing the Electronics category updated the revenue tile from $1,839,455.69 to $630,444.04 and showed 602 orders, one category bar and 50 table rows, without reloading the page.
>
> **What didn't work at first:** for the first few minutes after the service was created, Render returned intermittent 404s (`x-render-routing: no-server`) while the new service spread across its network. That cleared on its own, and I confirmed 20 successful loads in a row before running the tests above.
>
> **Limitations:**
> - **Sleep on the free plan:** the service sleeps after 15 minutes without traffic, so the first request after that takes about 30–60 seconds.
> - **Updating the app:** you change the secret files in Render and redeploy, because there's no repo to push to. If the code is later pushed to GitHub, the `render.yaml` blueprint already describes a git-based deploy.

## Shell commands during deploy

- `6s` `cd /home/runner/work/_temp/adb-lt4yb-dataviz; git status --short; git log --oneline | head; git remote -v; gh auth status 2>&1 | head -2`
- `20s` `cd /home/runner/work/_temp/adb-lt4yb-dataviz; wc -c data/sales.csv server.js lib.js public/index.html; grep -n "index.html'))" server.js`
- `26s` `cd /home/runner/work/_temp/adb-lt4yb-dataviz; sed -i "15s#.*#const INDEX = fs.readFileSync(process.env.INDEX_FILE || path.join(__dirname, 'public', 'index.html'));#" server.js; npm test 2>&1 | grep -E`
- `34s` `for i in $(seq 1 30); do st=$(curl -sS -H "Authorization: Bearer $RENDER_API_KEY" "https://api.render.com/v1/services/srv-dbfrd3ijnfac738kivq0/deploys?limit=1" | python3 -c 'import json,sys; print(jso`
- `47s` `cd /home/runner/work/_temp/adb-lt4yb-dataviz; U=https://adb-lt4yb-dataviz-web.onrender.com; scripts/smoke.sh $U; curl -sS "$U/api/summary?region=West&category=Software&start=2025-06-01&end=2025-08-31"`
- `53s` ❌ `cd /home/runner/work/_temp/adb-lt4yb-dataviz; U=https://adb-lt4yb-dataviz-web.onrender.com; for i in 1 2 3; do curl -sS -o /dev/null -w '%{http_code} ' $U/; done; echo; scripts/smoke.sh $U`
- `57s` `U=https://adb-lt4yb-dataviz-web.onrender.com; for i in 1 2 3 4; do curl -sS -D - $U/ -o /tmp/o.txt | grep -iE '^(HTTP|x-render|rndr|content-type|server)'; head -c 150 /tmp/o.txt; echo; echo ---; done`
- `1m 01s` ❌ `sleep 150; U=https://adb-lt4yb-dataviz-web.onrender.com; for i in $(seq 1 20); do curl -sS -o /dev/null -w '%{http_code} ' $U/; done; echo`
- `1m 04s` `U=https://adb-lt4yb-dataviz-web.onrender.com; ok=0; until [ $ok -ge 20 ]; do c=$(curl -sS -o /dev/null -w '%{http_code}' $U/); if [ "$c" = 200 ]; then ok=$((ok+1)); else ok=0; sleep 5; fi; done; echo `
- `1m 09s` `cd /home/runner/work/_temp/adb-lt4yb-dataviz; cat > deployment.json <<'EOF'`
- `1m 13s` `until [ -s /tmp/claude-1001/-home-runner-work--temp-adb-lt4yb-dataviz/f4cd8b54-5c41-439e-836a-539f96c72e84/tasks/bccph9tzs.output ]; do sleep 5; done; cat /tmp/claude-1001/-home-runner-work--temp-adb-`
- `4m 23s` ❌ `cd /home/runner/work/_temp/adb-lt4yb-dataviz; U=https://adb-lt4yb-dataviz-web.onrender.com; scripts/smoke.sh $U`
