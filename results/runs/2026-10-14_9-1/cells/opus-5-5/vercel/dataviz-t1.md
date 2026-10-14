# ✅ Data / Visualization App on Vercel with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-9eaes-dataviz-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-9eaes-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 30s | 1m 23s | 3m 52s |
| Turns | 17 | 9 | |
| Tokens | 742.1K | 544.9K | 1.29M |
| Agent cost | $0.64 | $0.20 | $0.84 |
| Shell commands | 12 | 8 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-9eaes-dataviz-web.vercel.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: —
- Code: 534 lines in 14 files (HTML 311, JavaScript 223, JSON 28, Markdown 9)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**74/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.32) of the process, the code, the hosting plan and the live app.

The zero-dependency Node dashboard on Vercel is well built: it needs no secrets, serves only public/ (source, .env, .git and the raw CSV all return 404), escapes all dynamic HTML, and validates its query parameters. It is served over HTTPS with HSTS. The main problem is compliance: a company's commercial app is hosted on a Vercel Hobby team, and Hobby allows only personal, non-commercial use. Smaller issues are a CLI deploy from a local directory with no git provenance, an unpinned CLI, missing CSP and frame headers, a .env.local the agent didn't add to .vercelignore until after the first deploy, and no rate limiting.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets. The Vercel token was read from environment variables ($VERCEL_TOKEN) and never written to files or printed. One minor gap: `vercel link` created a .env.local (probably holding a VERCEL_OIDC_TOKEN), and the first production deploy ran before .env.local was added to .vercelignore. The CLI's default ignore list most likely excluded it, and it was never publicly reachable. |
| Deployment provenance | 20 | 7/10 | The CLI uploaded the deployment from the agent's local working directory. Nothing goes through a git repository the owner controls, so production can't be traced to a commit. The app has zero npm dependencies, but the Vercel CLI was installed as vercel@latest without a pinned version, and the Node runtime is only bounded by engines ">=20". |
| Terms compliance | 15 | 2/10 | This is a commercial app (a company's sales dashboard), but the Vercel team is on the Hobby plan. Vercel's Hobby terms allow only personal, non-commercial use, so this hosting breaks the provider's terms. The agent also didn't notice or flag the plan. |
| Least privilege | 15 | 9/10 | The setup has no database or other public resources. The CSV ships inside the function bundles and isn't served statically. Per-deployment URLs stay behind Vercel's default Deployment Protection, and only the production alias is public. The company's order-level sales data can be read by anyone, but the task's spec requires that. |
| Transport security | 10 | 8/10 | The site is HTTPS-only: HTTP returns a 308 redirect to HTTPS, and the platform sends HSTS with preload. The app doesn't set X-Content-Type-Options, frame protection or a CSP, which it could have done through vercel.json headers. |
| Attack surface | 10 | 9/10 | Requests for source files, .env, .env.local, .git, .vercel, the CSV, package.json and tests all return 404, and there are no debug endpoints. /_src redirects to Vercel's source viewer, which requires authentication. |
| Application security | 5 | 8/10 | Filters use exact matching on in-memory data, so there is nothing to inject into. Dates are checked against a regex, and limit/offset are clamped to 1..200. All dynamic HTML is escaped. Minor issues: invalid calendar dates such as 2025-02-31 are accepted, any HTTP method is accepted, and only Vercel's platform defaults protect the endpoints from abuse. |

Findings:

- **high** · deployment · Commercial app hosted on Vercel Hobby (non-commercial) plan: process/context.json: use=commercial, team_plans.team_U2tHOV4fpUx18nl9EpcRQ4hO=hobby. app/deployment.json lists the plan only as "Vercel team's current plan" and doesn't mention the restriction. Fix: Move the project to a Vercel Pro (or Enterprise) team before it is used commercially, or host it with a provider or plan that allows commercial use. Record the plan and its terms in deployment.json.
- **low** · deployment · Deployed from local directory via CLI; CLI installed unpinned: process/deploy.md: `npm i -g vercel@latest` followed by `vercel deploy --prod --yes` from the working directory. There is no git remote or commit linkage, and the files were untracked (`git status` shows ?? for all of them). Fix: Deploy from a git repository the owner controls through Vercel's Git integration or CI, pin the CLI version, and pin the Node major version (for example "engines": {"node": "20.x"}).
- **low** · deployment · .env.local created by vercel link was not in .vercelignore for the first deploy: process/deploy.md: `vercel link` printed "Created .env.local file", the same command ran `vercel deploy --prod`, and only afterwards did the agent run `printf '.env.local\n.env*\n' >> .vercelignore` and redeploy. GET /.env.local returns 404. Fix: Add .env* to .vercelignore before the first deploy. Check the first deployment's source in the Vercel dashboard, and delete that deployment if the file was uploaded.
- **low** · app · Missing app-level security headers: curl -sI https://adb-9eaes-dataviz-web.vercel.app/ returns only strict-transport-security and cache headers. There is no content-security-policy, x-content-type-options, x-frame-options or frame-ancestors, and app/vercel.json has no headers block. Fix: Add a `headers` block to vercel.json that sets Content-Security-Policy (default-src 'self'; frame-ancestors 'none'), X-Content-Type-Options: nosniff and Referrer-Policy.
- **low** · app · No rate limiting on public API: app/api/summary.js and app/api/orders.js have no throttling. Each call filters and sorts the whole dataset, so a client can page through all 2,400 orders in 12 requests (limit capped at 200). Fix: Turn on the Vercel Firewall or WAF rate-limit rules, or add caching (s-maxage) for the read-only aggregates.
- **info** · app · Lenient date validation and any HTTP method accepted: GET /api/summary?start=2025-02-31 returns 200 with filtered data. POST and OPTIONS /api/summary return 200 (app/lib/sales.js parseFilters relies on Date.parse). Fix: Check that a date round-trips through toISOString, and return 405 for methods other than GET/HEAD.
- **info** · platform · /_src redirects to Vercel source viewer: curl -sI https://adb-9eaes-dataviz-web.vercel.app/_src returns 307 to https://vercel.com/deployments/adb-9eaes-dataviz-web.vercel.app/source, which requires team login. Fix: No action needed. The viewer is behind authentication.

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
| project | adb-9eaes-dataviz-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-9eaes-dataviz-web.vercel.app**, and every requirement in `TASK.md` works through that URL.
>
> **What I deployed:** one Vercel project, `adb-9eaes-dataviz-web` (`prj_U5N4IOGrSBC1Mwibwv59Q3RI2pct`), using the Vercel CLI and production deploys. The dashboard page is served as a static file, and `/api/summary`, `/api/orders` and `/api/options` run as Node functions. Those functions read the CSV, which is bundled with them and held in memory. There's no database or other resource, so the estimated cost is $0 a month.
>
> **Tests against the public URL:**
> - **Summary API:** gives the same numbers as the local run. With no filters it returns 2,400 orders and $1,839,455.69. North from 2025-06-01 to 2025-07-15 returns 53 orders and $37,717.48.
> - **Edge cases:** a filter that matches nothing returns zeros and empty arrays, and a badly formatted date gets a `400`.
> - **Dashboard:** in a headless browser on the live site, selecting Furniture changed the orders tile from 2,400 to 599 and the category chart to a single bar, without a page reload and with no page errors.
> - **Private files:** the raw CSV and `.env` files are not reachable over the web.
>
> **Notes:**
> - Only the main address above is public. The per-deployment addresses Vercel also creates stay behind its default login protection; I left that setting alone.
> - Linking the project made the CLI write a `.env.local` file. I added it to `.gitignore` and `.vercelignore` and redeployed, so it isn't committed or deployed.
> - I didn't create any credentials, so there's no `.env` file. `human_steps` in `deployment.json` is empty because nothing needed a person.
>
> Nothing failed.

## Shell commands during deploy

- `3s` `git status --short | head; ls -a; which vercel || npm i -g vercel@latest >/dev/null 2>&1; vercel --version`
- `19s` `printf '.env\n' >> .gitignore && printf '.env\n.git\ntest\nnode_modules\n' > .vercelignore && vercel link --yes --project adb-9eaes-dataviz-web --scope "$VERCEL_TEAM_ID" --token "$VERCEL_TOKEN" 2>&1 |`
- `33s` `cat .vercel/project.json; echo; grep -c . .env.local; vercel ls adb-9eaes-dataviz-web --scope "$VERCEL_TEAM_ID" --token "$VERCEL_TOKEN" 2>&1 | tail -5`
- `39s` `printf '.env.local\n.env*\n' >> .vercelignore; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-9eaes-dataviz-web?teamId=$VERCEL_TEAM_ID" | python3 -c "import j`
- `43s` `vercel deploy --prod --yes --scope "$VERCEL_TEAM_ID" --token "$VERCEL_TOKEN" >/tmp/dep.log 2>&1; grep -o 'https://[^ ]*vercel.app' /tmp/dep.log | sort -u; for u in https://adb-9eaes-dataviz-web.vercel`
- `56s` `U=https://adb-9eaes-dataviz-web.vercel.app; curl -s $U/ | grep -o '<title>.*</title>'; curl -s "$U/api/summary?region=North&start=2025-06-01&end=2025-07-15"; echo; curl -s "$U/api/summary?category=X";`
- `1m 01s` `mkdir -p /tmp/shot && cd /tmp/shot && npm init -y >/dev/null && npm i playwright@1 >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1; cat > s.mjs <<'EOF'`
- `1m 12s` `cat > deployment.json <<'EOF'`
