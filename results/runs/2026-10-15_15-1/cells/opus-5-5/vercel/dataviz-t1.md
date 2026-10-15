# ✅ Data / Visualization App on Vercel with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-hjs6l-dataviz-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-hjs6l-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 21s | 1m 10s | 6m 40s |
| Turns | 15 | 10 | |
| Tokens | 575.3K | 768.7K | 3.04M |
| Agent cost | $0.58 | $0.27 | $1.54 |
| Shell commands | 10 | 8 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 3m 10s, 1.70M tokens, $0.68).

## Screenshots

**The dashboard** (https://adb-hjs6l-dataviz-web.vercel.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Runtime: Node.js 24
- Frameworks: Plain Vercel Functions
- Packaging: vercel.json
- Hosting: Vercel project (node), Vercel Functions
- Code: 524 lines in 17 files (HTML 277, JavaScript 216, JSON 31, Shell 31, Markdown 23)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

### Stack fit

**93/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

The stack is static HTML plus zero-dependency Node functions on Vercel, with the CSV kept in memory. That is a proportionate, well-reasoned fit for a small read-only dashboard and plays directly to Vercel's static-plus-functions model.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | The data is a read-only 2,400-row CSV, so loading it into memory inside a stateless function is durable and correct. The static HTML with vanilla JS and hand-built SVG charts covers the filters, KPIs, the two charts and the paginated table without page reloads. |
| Proportion | 30 | 10/10 | There is no framework, build step, database or runtime dependency, so the stack is about as small as the requirements allow. STACK.md reasons soundly about rejecting Next.js and a database, and the build followed it. |
| Platform fit | 30 | 9/10 | It uses Vercel's native layout: static files from public/ and Node functions in api/, with includeFiles bundling the CSV. The only friction was Vercel auto-detecting a Node server, which `framework: null` fixed. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**77/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.34) of the process, the code, the hosting plan and the live app.

The dashboard is a small, cleanly built static page with three zero-dependency Node functions. It handles secrets well, exposes nothing beyond the app, validates input and escapes output, and is served over HTTPS with HSTS. The main problem is compliance: this business app runs on a Vercel Hobby team, and Hobby's terms allow only non-commercial use. Smaller issues are the unpinned `vercel@latest` CLI, a direct upload with no commit behind it, and missing security headers that vercel.json could have set.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets, and no credential appears in source, the transcripts or deployed files; .env/.env.local (created by `vercel link`) are excluded from upload and git. A minor weakness: the Vercel token is passed as a `--token` command-line argument, so other local processes could see it. |
| Deployment provenance | 20 | 7/10 | Vercel built production directly from the agent's uploaded workspace. There are no dependencies to pin, but the deploy CLI is fetched unpinned (`npx -y vercel@latest`), and the deployment isn't tied to a commit in a repository the owner controls. |
| Terms compliance | 15 | 2/10 | The app is for a business (`use: commercial`), but it is deployed on a team whose plan is Hobby. Vercel's terms and Fair Use Guidelines limit Hobby to personal, non-commercial use. The agent reported 'Team's existing plan' without checking it. |
| Least privilege | 15 | 10/10 | The deployment is one project with a public static page and three read-only functions. There is no data store, no extra resources and no write paths. The bundled CSV is reachable only through the functions. |
| Transport security | 10 | 8/10 | Served only over HTTPS with a valid certificate. HTTP gets a 308 redirect to HTTPS, and HSTS (with preload) is on. X-Content-Type-Options, frame protection and CSP are missing; the agent could have added them with `headers` in vercel.json. |
| Attack surface | 10 | 10/10 | Probes for .env, .env.local, .git, package.json, vercel.json, server.js, lib/, scripts/, data/sales.csv and .vercel/ all returned 404. Errors are short JSON messages with no stack traces. |
| Application security | 5 | 9/10 | Dates are strictly validated (bad ones get a 400), limit and offset are clamped, filters are exact-match comparisons on in-memory rows, and the client escapes data before inserting it into HTML. Nothing in the app limits request rates on the public endpoints, which matters little for this read-only, low-cost data. |

Findings:

- **high** · deployment · Commercial app hosted on a Vercel Hobby (non-commercial) plan: process/context.json: use=commercial, team_plans.team_U2tHOV4fpUx18nl9EpcRQ4hO=hobby; process/deployment.json plan: "Team's existing plan; usage fits within free/included limits" Fix: Move the project to a Pro (or Enterprise) team before using it for business, or host it on a plan whose terms allow commercial use.
- **low** · deployment · Deploy CLI is fetched unpinned at deploy time: app/scripts/deploy.sh line 8: VC="npx -y vercel@latest --token $VERCEL_TOKEN ..."; process/deploy.md deploy commands use `npx -y vercel@latest` Fix: Pin the CLI version (for example vercel@62.7.0) in package.json devDependencies or in the npx call.
- **low** · deployment · Production is a direct upload from the local workspace, with no commit behind it: process/deploy.md: `vercel deploy --prod --yes` from /home/runner/work/_temp/adb-hjs6l-dataviz; no git repository was initialized Fix: Deploy from a git repository the owner controls (Vercel Git integration or CI), so each production build traces to a commit.
- **low** · deployment · Vercel token passed as a command-line argument: app/scripts/deploy.sh line 8 and process/deploy.md: `npx -y vercel@latest --token "$VERCEL_TOKEN" ...` Fix: Let the CLI read VERCEL_TOKEN from the environment instead of passing --token, which can show up in process listings.
- **low** · deployment · Missing security headers: curl -sI https://adb-hjs6l-dataviz-web.vercel.app/ returns strict-transport-security, but no x-content-type-options, x-frame-options/frame-ancestors or content-security-policy; app/vercel.json defines no headers Fix: Add a `headers` block to vercel.json setting X-Content-Type-Options: nosniff, a Content-Security-Policy with frame-ancestors 'none' (or X-Frame-Options: DENY), and a Referrer-Policy.
- **info** · app · No rate limiting on public API endpoints: app/api/summary.js and app/api/orders.js handle every request with no throttling; /api/orders allows limit up to 500 (app/api/orders.js line 6) Fix: Optionally turn on Vercel Firewall rate-limit rules for /api/*; the read-only data and small payloads keep the risk low.
- **info** · platform · Vercel source-view path exists, but it requires a login: curl -sI https://adb-hjs6l-dataviz-web.vercel.app/_src returns 307, Location: https://vercel.com/deployments/adb-hjs6l-dataviz-web.vercel.app/source Fix: No action needed; the Vercel dashboard limits source view to team members.
- **info** · platform · Wildcard CORS on static assets: curl -sI / shows access-control-allow-origin: * (Vercel's default for static files) Fix: Acceptable for a public dashboard; override it in vercel.json headers if cross-origin reads should be blocked.

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
| project | adb-hjs6l-dataviz-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-hjs6l-dataviz-web.vercel.app**. I tested every requirement in `TASK.md` through that public URL, and they all pass.
>
> **What's deployed:** one Vercel project, `adb-hjs6l-dataviz-web` (`prj_mOcxTvcPRSCyRhP6Va1aI7WZ5f2J`). It serves the dashboard page as a static file, and three small Node.js functions handle the data requests by reading the bundled `sales.csv`. There's no database or anything else to pay for, so the estimated cost is $0 a month.
>
> **What I checked on the live site:**
> - **Dashboard:** loads publicly with no login. In headless Chrome, filtering by Software, April to September, updated the totals, both charts and the orders table.
> - **`/api/summary` with no filters:** 2,400 orders and 1,839,455.69 in revenue, matching the local results.
> - **`/api/summary` with region, category and dates combined:** returns exactly the expected numbers.
> - **No matching rows:** returns zeros and empty arrays.
> - **Orders list:** pages through results correctly.
> - **Badly formed date:** returns a `400` error.
>
> **One problem fixed along the way:** the first deploy failed because Vercel assumed this was a Node server app and looked for a server file to start. Setting `"framework": null` in `vercel.json` fixed it, and the second deploy succeeded.
>
> **Secrets:** I didn't create any new credentials, so `.env` wasn't needed. The token isn't written in any file; I searched the project to confirm. Linking the project made Vercel create a `.env.local` file; it is excluded from both git and the upload.
>
> To redeploy, run `./scripts/deploy.sh`, and to re-check the live site, run `./scripts/smoke.sh <url>`. `deployment.json` is written, with no human steps left.

## Shell commands during deploy

- `4s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; [ -n "$VERCEL_TOKEN" ] && echo token-set; [ -n "$VERCEL_TEAM_ID" ] && echo team-set; ls -a; cat scripts/deploy.sh | head -12`
- `10s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; sed -i 's#^VC="npx -y vercel@latest --token $VERCEL_TOKEN"#VC="npx -y vercel@latest --token $VERCEL_TOKEN ${VERCEL_TEAM_ID:+--scope $VERCEL_TEAM_ID}"#' sc`
- `15s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; npx -y vercel@latest --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" deploy --prod --yes < /dev/null > /tmp/dep.out 2>/tmp/dep.err; echo exit=$?; cat /t`
- `27s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-hjs6l-dataviz-web?teamId=$VERCEL_TEAM_ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print({k:d.get(k`
- `32s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; cat > vercel.json <<'EOF'`
- `45s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; U=https://adb-hjs6l-dataviz-web.vercel.app; ./scripts/smoke.sh $U; curl -s -o /dev/null -w "/ %{http_code}\n" $U/; curl -s -w "\n%{http_code}\n" "$U/api/s`
- `51s` `cd /tmp; google-chrome --headless=new --no-sandbox --window-size=1280,900 --virtual-time-budget=5000 --screenshot=/tmp/live.png "https://adb-hjs6l-dataviz-web.vercel.app/?category=Software&start=2025-`
- `1m 02s` `cd /home/runner/work/_temp/adb-hjs6l-dataviz; cat > deployment.json <<'EOF'`
