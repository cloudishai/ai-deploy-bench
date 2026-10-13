# ✅ Data / Visualization App on Vercel with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-ikpsc-dataviz-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-ikpsc-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 14s | 1m 03s | 3m 17s |
| Turns | 14 | 7 | |
| Tokens | 591.4K | 410.2K | 1.00M |
| Agent cost | $0.58 | $0.15 | $0.73 |
| Shell commands | 10 | 5 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-ikpsc-dataviz-web.vercel.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: —
- Code: 491 lines in 13 files (HTML 261, JavaScript 230, JSON 28, Markdown 13)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**73/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.29) of the process, the code, the hosting plan and the live app.

The deployment is technically clean: no secrets, no npm dependencies, strict input validation, HTTPS with HSTS, and no source, config or data files exposed. Its main problem is compliance: a commercial business app is hosted on a Vercel Hobby team, whose terms allow only personal, non-commercial use. The other issues are minor: a CLI upload from the agent's workstation with no owner-controlled repository, an unpinned CLI and Node runtime, and missing CSP, nosniff and frame-protection headers that the project could have set.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets, and none are in the source, the deployed files or the logs; the Vercel token stayed in an env var. One minor point: it was passed as a --token argument, which shows up in the process list. |
| Deployment provenance | 20 | 6/10 | The app has no npm dependencies and deploys exactly the local source, but it was uploaded straight from the agent's workstation with the CLI, not from a repository the owner controls. The CLI was installed as vercel@latest and the Node runtime floats (engines >=18). |
| Terms compliance | 15 | 2/10 | The app is for a business (use: commercial), but it runs on a Vercel Hobby team. Vercel's Hobby terms limit that plan to personal, non-commercial use, so this hosting breaks the plan's terms. The agent never checked or flagged the plan. |
| Least privilege | 15 | 9/10 | It is a static site plus stateless serverless functions, with no database, storage or other extra resources. The read-only CSV is bundled into the functions and is not served as a static file. Vercel's default wildcard CORS on static assets is the only broad setting. |
| Transport security | 10 | 8/10 | HTTPS works with a valid certificate, HTTP gets a 308 redirect to HTTPS, and Vercel sends HSTS with preload. The agent could have set X-Content-Type-Options, frame protection and a CSP in vercel.json but didn't. |
| Attack surface | 10 | 10/10 | Requests for .env, .git/config, package.json, vercel.json, the lib/server/test sources, data/sales.csv and .vercel/project.json all return 404. Errors are short JSON messages with no stack traces, and there are no debug or admin endpoints. |
| Application security | 5 | 8/10 | Dates are strictly validated (400 on a malformed or impossible date), filters are exact-match against in-memory data so there is nothing to inject into, page size is capped at 200, and the client escapes values before using innerHTML. The public API has no rate limiting, which is minor. |

Findings:

- **high** · deployment · Commercial app hosted on a Vercel Hobby (non-commercial) plan: process/context.json: use=commercial, team_plans.team_U2tHOV4fpUx18nl9EpcRQ4hO=hobby. process/deployment.json describes the plan only as "Team's existing Vercel plan (usage well within included/free limits)" and doesn't flag the restriction. Fix: Move the project to a Vercel Pro (or Enterprise) team, or to another host whose plan allows commercial use.
- **medium** · deployment · Deployed by CLI upload from the local workstation, with no owner-controlled source: process/deploy.md: `vercel deploy --prod --yes --token "$VERCEL_TOKEN"` run from the local directory; no Git repository is connected to the project. Fix: Push the code to a repository the owner controls and deploy through Vercel's Git integration or a CI pipeline, so every production build traces back to a commit.
- **low** · deployment · Unpinned deploy tool and Node runtime: process/deploy.md: `npm i -g vercel@latest`; app/package.json: "engines": { "node": ">=18" }. Vercel warns that this will auto-upgrade on new major Node releases. Fix: Pin the CLI version (e.g. vercel@64.0.2) and set an exact Node major version (e.g. "22.x").
- **low** · deployment · Missing security headers the project could set: curl -sI https://adb-ikpsc-dataviz-web.vercel.app/ returns strict-transport-security but no content-security-policy, x-content-type-options or x-frame-options; app/vercel.json has no headers block. Fix: Add a `headers` entry in vercel.json with Content-Security-Policy (the page uses only inline script/style, so a self/inline policy is enough), X-Content-Type-Options: nosniff and frame-ancestors 'none' / X-Frame-Options: DENY.
- **low** · deployment · Vercel token passed as a command-line argument: process/deploy.md: `vercel project add ... --token "$VERCEL_TOKEN"` and `vercel deploy --prod --yes --token "$VERCEL_TOKEN"`; the value was masked in the transcript, but it ends up in the process argv. Fix: Let the CLI read VERCEL_TOKEN from the environment instead of passing --token.
- **low** · app · No rate limiting on public API endpoints: app/api/summary.js and app/api/orders.js serve every request with no throttling; /api/orders?page_size=200 pages through all 2,400 order lines. Fix: Turn on Vercel Firewall rate-limiting rules (available on paid plans) or add lightweight throttling if the API is expected to see abuse.
- **info** · platform · Wildcard CORS on static assets: curl -sI https://adb-ikpsc-dataviz-web.vercel.app/ returns access-control-allow-origin: *; the API responses don't include it. Fix: No action is needed for a public dashboard. If cross-origin reads should be restricted, override the header in vercel.json.
- **info** · deployment · Source, config and data files are not served: GET /.env, /.git/config, /package.json, /vercel.json, /lib/sales.js, /data/sales.csv, /server.js, /test/api.test.js and /.vercel/project.json all return 404; /api/nope returns 404; /api/summary.js runs the function instead of returning its source. Fix: None.

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
| Light use | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $0.00 of usage |
| Busy | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $5.75 of usage |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-ikpsc-dataviz-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-ikpsc-dataviz-web.vercel.app**, and every requirement in `TASK.md` that I tested works through that URL.
>
> **What's deployed:** one Vercel project, `adb-ikpsc-dataviz-web` (id `prj_3mDXVCUHBnkCZquNwsMTXFQmDgwk`). It serves the dashboard page as a static file and runs the API as serverless functions. There's no database: the CSV is packaged with the functions and kept in memory. I estimate the cost at $0 a month.
>
> **What I tested on the public URL:**
> - **Dashboard (`/`):** returns 200 over HTTPS, and a headless Chrome screenshot shows the filters, KPI tiles, both charts and the orders table drawing correctly.
> - **`/api/summary` with no filters:** $1,839,455.69 revenue, 2,400 orders and 15,179 units, the same as the local run and the CSV.
> - **`/api/summary` with all four filters:** North, Software and June 2025 together give 11 orders and $12,566.26.
> - **No matches:** a region that doesn't exist returns zeros and empty arrays.
> - **Bad date:** a malformed `start` returns 400.
> - **`/api/orders` and `/api/options`:** both respond correctly.
>
> I didn't click through the filters in a browser on the live site, so that path is covered only by testing the API calls it makes.
>
> I didn't create any credentials, so there's no `.env`. Nothing needed a person, so `human_steps` in `deployment.json` is empty.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-ikpsc-dataviz; which vercel || npm i -g vercel@latest >/dev/null 2>&1; vercel --version; mkdir -p .vercel; cat >> .gitignore <<'EOF'`
- `29s` `cd /home/runner/work/_temp/adb-ikpsc-dataviz; vercel link --yes --project adb-ikpsc-dataviz-web --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" >/dev/null 2>&1; cat .vercel/project.json; echo; verce`
- `45s` `U=https://adb-ikpsc-dataviz-web.vercel.app; curl -s -o /dev/null -w '%{http_code} ' $U/; curl -s $U/ | grep -o '<title>.*</title>'; curl -s $U/api/summary | head -c 200; echo; curl -s "$U/api/summary?`
- `50s` `cd /tmp; google-chrome --headless=new --no-sandbox --disable-gpu --window-size=1300,700 --virtual-time-budget=5000 --screenshot=/tmp/prod.png https://adb-ikpsc-dataviz-web.vercel.app/ 2>/dev/null; ls `
- `57s` `cd /home/runner/work/_temp/adb-ikpsc-dataviz; cat > deployment.json <<'EOF'`
