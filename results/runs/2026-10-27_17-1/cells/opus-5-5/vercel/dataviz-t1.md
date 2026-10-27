# ✅ Data / Visualization App on Vercel with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-e9y2h-dataviz-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-e9y2h-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 31s | 49s | 5m 45s |
| Turns | 16 | 7 | |
| Tokens | 653.4K | 489.5K | 1.94M |
| Agent cost | $0.61 | $0.17 | $1.09 |
| Shell commands | 12 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 2m 26s, 801.6K tokens, $0.30).

## Screenshots

**The dashboard** (https://adb-e9y2h-dataviz-web.vercel.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 20+
- Frameworks: Plain Vercel Functions
- Packaging: vercel.json
- Hosting: Vercel project, Vercel Functions
- Code: 489 lines in 15 files (JavaScript 391, HTML 98, JSON 25, Markdown 19)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Static HTML/JS on Vercel's CDN plus zero-dependency Node functions that read a bundled CSV into memory fits this read-only dashboard and maps directly onto Vercel's model. The build matches the reasoning in STACK.md.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | Keeping a 2,400-row read-only CSV in memory is appropriate, as the task explicitly allows. The static page with vanilla JS and SVG charts meets every dashboard requirement, and fetch-based updates avoid full page reloads. |
| Proportion | 30 | 9/10 | There are no npm dependencies, no framework, no build step and no database. That is about as simple as the requirements allow, and it isn't a stand-in that only appears to work. Hand-rolling the charts costs some code but no dependencies. |
| Platform fit | 30 | 9/10 | It uses Vercel's native conventions: the CDN serves public/, files in api/*.js become functions, and includeFiles bundles the CSV. Cold starts stay light, and there is no long-running server. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**75/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.33) of the process, the code, the hosting plan and the live app.

This is a small, zero-dependency sales dashboard on Vercel: static files plus three read-only Node functions over a bundled CSV. There are no secrets in the app, nothing is exposed beyond the app, HTTPS is enforced and input validation is solid. The main problem is compliance: a commercial app is running on a Vercel Hobby team, whose terms forbid commercial use. Lesser issues are the unpinned `vercel@latest` CLI deploying from a temp copy, and security headers the agent could have set in vercel.json but didn't.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets, and none appear in the source, the deployed files or the logs. The Vercel token was read from $VERCEL_TOKEN, and the output was filtered with grep -v token. The one blemish is that the token was passed as a --token command-line argument, which makes it visible in the process list. |
| Deployment provenance | 20 | 7/10 | There are no npm dependencies and no build step, and the agent deployed exactly the files it built and tested. However, it deployed from an ad-hoc /tmp copy with an unpinned `npx -y vercel@latest` CLI, not from a git source the owner controls. |
| Terms compliance | 15 | 2/10 | process/context.json says the use is commercial, but the team is on Vercel's Hobby plan. Vercel's terms limit Hobby to personal, non-commercial use, so a business's sales dashboard needs a Pro plan. |
| Least privilege | 15 | 9/10 | There is only one Vercel project: static files plus three read-only functions, with no data stores, no extra services and no credentials at runtime. The production alias is public, which the task requires, and preview URLs keep the team's Deployment Protection. |
| Transport security | 10 | 8/10 | HTTP returns a 308 redirect to HTTPS, the platform's certificate is valid and the platform sends HSTS with preload. The agent did not add X-Content-Type-Options, frame protection or a CSP, which it could have set in vercel.json. |
| Attack surface | 10 | 10/10 | Requests for /.env, /.git/config, /package.json, /server.js, /lib/data.js, /data/sales.csv, /vercel.json and /test files all return 404. Error responses are generic, with no stack traces, and /_src redirects to the auth-gated Vercel dashboard. |
| Application security | 5 | 8/10 | Dates are strictly validated (2025-02-30 returns 400), the limit is clamped to 1–500, the offset can't go below 0, filtering is exact-match in memory with nothing to inject into, and the table uses textContent. Minor issues: the chart tooltips use innerHTML with CSV-derived strings, and the public endpoints have no rate limiting of their own. |

Findings:

- **high** · deployment · Commercial app hosted on Vercel Hobby (non-commercial) plan: process/context.json: "use": "commercial", team_plans {"team_U2tHOV4fpUx18nl9EpcRQ4hO": "hobby"}; process/deployment.json describes the plan as "Team's existing plan; usage within free/included limits". Vercel's Hobby terms restrict it to personal, non-commercial use. Fix: Move the project to a Vercel Pro (or Enterprise) team before using it for the business. In the meantime, record the plan constraint in deployment.json and human_steps.
- **low** · deployment · Unpinned Vercel CLI and deploy from a local temp copy: process/deploy.md: `cp -r api lib public data package.json vercel.json $S/; cd $S; npx -y vercel@latest deploy --prod --yes --token "$VERCEL_TOKEN" ...` (CLI 65.3.1 resolved at run time) Fix: Pin the CLI version (e.g. npx vercel@65.3.1) and deploy from a git repository connected to the project, so that every production build traces back to a commit.
- **low** · deployment · Vercel token passed as a command-line argument: process/deploy.md: `npx -y vercel@latest deploy --prod --yes --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID"`. The value came from the environment and was not printed, but the expanded argument is visible to other processes on the host. Fix: Let the CLI read VERCEL_TOKEN from the environment instead of passing it with --token.
- **low** · deployment · No X-Content-Type-Options, frame protection or CSP headers: curl -sI https://adb-e9y2h-dataviz-web.vercel.app/ returns only strict-transport-security, cache-control, content-type and access-control-allow-origin: *. app/vercel.json has no `headers` block. Fix: Add a `headers` entry in vercel.json for X-Content-Type-Options: nosniff, X-Frame-Options: DENY (or CSP frame-ancestors 'none') and a restrictive Content-Security-Policy (default-src 'self').
- **info** · app · Tooltip renders API strings via innerHTML: app/public/app.js:38 `tip.innerHTML = html`; line 118 interpolates `${d.category}` from /api/summary. The values come from the bundled, read-only CSV, so this can't be exploited today. Fix: Build the tooltip with textContent and DOM nodes, or escape the interpolated values.
- **info** · app · No application-level rate limiting on public API: app/api/summary.js and app/api/orders.js accept any number of unauthenticated requests. Each request is a cheap in-memory filter over 2,400 rows, and Vercel's platform DDoS mitigation applies. Fix: Optionally add Vercel WAF rate-limit rules, or edge caching (s-maxage) for the read-only responses, to limit function invocations.

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
| project | adb-e9y2h-dataviz-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The sales dashboard is live at **https://adb-e9y2h-dataviz-web.vercel.app**, and everything I tested through that public URL works.
>
> **What's deployed:** one new Vercel project, `adb-e9y2h-dataviz-web` (`prj_MWfERpN40iju5ETSEI00L43vsA39`), in the team you provided. It serves the dashboard page as static files and runs the three API endpoints as serverless functions with the CSV bundled in. There's no database and nothing else was created, so the expected cost is $0.
>
> **Tested through the public URL:**
> - The dashboard and its script both load (200).
> - With no filters, `/api/summary` returns $1,839,455.69 revenue, 2,400 orders and 15,179 units — the same as locally.
> - Combining all four filters (region, category, start and end date) returns the correct subset.
> - A filter that matches nothing returns zeros and empty arrays with a 200.
> - A malformed date returns 400 with an error message.
> - The orders endpoint returns the newest orders first.
> - In headless Chrome, the live page with West and Software selected shows KPIs that match the API ($214,203.52, 176 orders, 1,856 units) and the "1–50 of 176" table.
>
> The team's default deployment protection blocks the per-deployment preview URLs, but the main URL above is publicly reachable.
>
> `deployment.json` is written with no `human_steps`, and nothing failed. I didn't create any new credentials, so there's no `.env` file.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-e9y2h-dataviz; S=/tmp/adb-e9y2h-dataviz-web; rm -rf $S; mkdir -p $S; cp -r api lib public data package.json vercel.json $S/; cd $S`
- `8s` `grep -v -i token /tmp/d.out | head -20`
- `11s` ❌ `cd /tmp/adb-e9y2h-dataviz-web; timeout 400 npx -y vercel@latest deploy --prod --yes --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" --project adb-e9y2h-dataviz-web --create-if-missing </dev/null > /`
- `28s` `U=https://adb-e9y2h-dataviz-web.vercel.app`
- `35s` `cd /tmp; google-chrome --headless=new --no-sandbox --disable-gpu --virtual-time-budget=5000 --dump-dom 'https://adb-e9y2h-dataviz-web.vercel.app/?region=West&category=Software' 2>/dev/null | grep -oE `
- `43s` `cd /home/runner/work/_temp/adb-e9y2h-dataviz; cat > deployment.json <<'EOF'`
