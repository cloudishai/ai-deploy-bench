# ✅ Static Content Site on Vercel with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-qhvza-static-web.vercel.app (from deployment.json)
- Estimated hosting: $0.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-qhvza-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 14s | 1m 49s | 3m 03s |
| Turns | 7 | 8 | |
| Tokens | 253.9K | 340.9K | 594.9K |
| Agent cost | $0.41 | $0.15 | $0.57 |
| Shell commands | 6 | 7 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 368 lines in 15 files (HTML 166, JavaScript 164, CSS 38, JSON 24)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security review

**73/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.31) of the process, the code and the live app.

The Northwind Robotics site is a simple static site with one stateless validation function on Vercel. It exposes no source, env files or secrets, validates input correctly and avoids XSS. The main weaknesses: the app sets no security headers of its own (no CSP, nosniff or frame protection), the contact endpoint has no size or rate limits, and the deployment was uploaded from a local directory with unpinned tooling (`vercel@latest`). Minor secrets-hygiene lapses happened during deployment, and the agent cleaned up the one that mattered.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 8/10 | No secrets exist in the source or deployed files, and the token never appeared in transcript output. But the Vercel token was passed as a --token CLI argument, and the first deployment was uploaded before a .vercelignore existed, right after `vercel link` had written .env.local into the project directory. The agent spotted this and deleted that deployment. |
| Deployment provenance | 15 | 6/10 | The live site matches the reviewed source and has no third-party dependencies. However, it was uploaded from a local working directory with `npx -y vercel@latest` (an unpinned installer) instead of from a version-controlled source, and the Node runtime is unpinned (`engines: >=18`). |
| Transport security | 15 | 5/10 | HTTPS works with a valid certificate, HTTP 308-redirects to HTTPS, and Vercel adds HSTS. The app sets no headers of its own, so X-Content-Type-Options, frame protection (X-Frame-Options or frame-ancestors) and a Content-Security-Policy are all missing. |
| Attack surface | 15 | 9/10 | Only public/ and the function are served. .env, .git, .vercel, package.json, lib/, tests and the dev server all return 404, and errors don't leak stack traces. Static responses carry the platform default `Access-Control-Allow-Origin: *`, which is harmless for public content. |
| Application security | 20 | 7/10 | Validation is correct and type-checked, malformed JSON returns a clean 400, the client renders server messages with textContent (no XSS), and nothing is stored. The public endpoint has no length limits and no rate limiting, though: a 2 MB message was accepted with HTTP 200. |
| Least privilege | 10 | 9/10 | There is one Vercel project with a single stateless function, no data stores and no extra resources. The deployment-specific URL is protected by Vercel SSO, and the stale first deployment was deleted. The agent used a broad team token, but that was the credential it was given. |

Findings:

- **medium** · No app-defined security headers (CSP, X-Content-Type-Options, frame protection): app/vercel.json contains only cleanUrls/trailingSlash. `curl -sI https://adb-qhvza-static-web.vercel.app/` returns only strict-transport-security plus caching headers: no content-security-policy, x-content-type-options or x-frame-options. Fix: Add a `headers` block to vercel.json setting Content-Security-Policy (e.g. default-src 'self'; frame-ancestors 'none'), X-Content-Type-Options: nosniff, X-Frame-Options: DENY and Referrer-Policy.
- **low** · Contact endpoint has no input size limits or rate limiting: app/lib/validate.js checks only presence and format. POST /api/contact with a ~2 MB `message` returned {"ok":true} with HTTP 200. Nothing throttles repeated submissions. Fix: Cap the lengths of name, email and message (e.g. 100/254/5000 characters), reject non-JSON content types, and add rate limiting (Vercel Firewall rules or a per-IP limiter).
- **low** · First deployment uploaded before ignore rules existed, right after .env.local was created: process/deploy.md: `vercel link ... && vercel deploy --prod` printed 'Created .env.local file'. .vercelignore was added only in the next command. The agent then deleted dpl_HpQDu1PbN4iNc7tQ4xgTmdeqhF1b (the API returned state DELETED), and its URL now returns 404. Fix: Create .vercelignore (excluding .env*, .vercel and tests) before the first deploy, and avoid `vercel link` pulling env files into the upload directory.
- **low** · Vercel token passed as a command-line argument: process/deploy.md: `npx -y vercel@latest deploy --prod --yes --token "$VERCEL_TOKEN" ...`. The value was expanded from the environment and not printed, but it is visible in the process list. Fix: Have the CLI read the token from the VERCEL_TOKEN environment variable instead of passing --token.
- **low** · Unpinned deploy tooling and runtime; deployed from a local directory: process/deploy.md uses `npx -y vercel@latest`. app/package.json declares `"engines": { "node": ">=18" }`, and the build log warns it will auto-upgrade. The deployment was a CLI upload with no git source. Fix: Pin the Vercel CLI version (e.g. vercel@64.0.1) and the Node major version (e.g. "20.x"), and deploy from a git repository connected to the project so that each deployment maps to a commit.
- **info** · No sensitive files exposed: GET /.env, /.env.local, /.git/config, /.vercel/project.json, /package.json, /lib/validate.js, /dev-server.js, /test/app.test.js, /vercel.json and /TASK.md all return 404. /_src redirects to vercel.com, which requires authentication. GET /api/contact returns a JSON 405. Fix: None needed.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / returns HTML | yes | passed |  |
| GET /about returns HTML | yes | passed |  |
| GET /contact returns HTML | yes | passed |  |
| Home has an <h1> containing 'Northwind Robotics' | yes | passed |  |
| About has a heading containing 'About' | yes | passed |  |
| Contact has a form with name, email and message fields | yes | passed |  |
| Every page has a <title> and a viewport meta tag | no | passed |  |
| Home links to /about and /contact | no | passed |  |
| POST /api/contact with valid input returns {ok: true} | yes | passed |  |
| POST /api/contact rejects a bad email and an empty message with 400 | yes | passed |  |
| Unknown paths return 404 | yes | passed |  |
| Submitting the /contact form in a browser posts to /api/contact without leaving the page | yes | passed |  |
| Pages load in a browser without uncaught JavaScript errors | no | passed |  |

## Cloud resources

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-qhvza-static-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live at **https://adb-qhvza-static-web.vercel.app**, and every requirement in `TASK.md` works through that public URL. I checked each one with curl.
>
> - **What's deployed:** one Vercel project, `adb-qhvza-static-web` (`prj_r56AgZbGr83tvz9TfUSRMrmt35dU`). It serves the static pages from `public/` and runs `/api/contact` as a Node serverless function. It uses the free tier, so the cost is $0 a month.
> - **Pages:** `/`, `/about` and `/contact` return 200 with `text/html`. Each has a title, a viewport tag and navigation, and the home heading and contact form fields are all there.
> - **Paths:** unknown paths return 404. `/about.html` redirects (308) to `/about`.
> - **Contact endpoint:** valid input returns 200 `{"ok":true}`. A missing name, invalid email, empty message or broken JSON each return 400 with an error message.
> - **Cleanup:** the CLI made two deployments. The first went out before I added a `.vercelignore` to keep `.env*`, `.vercel` and the tests out of uploads. I deleted it in case it included the `.env.local` that `vercel link` had just created. The live site is the second deployment.
> - **Credentials:** I didn't create any, so there's no `.env`, and no secrets were printed or written to files.
> - **Records:** `deployment.json` is written. `human_steps` is empty because nothing needed a person.
>
> Nothing failed.

## Shell commands during deploy

- `3s` `(vercel --version || npx -y vercel@latest --version) 2>&1 | tail -2`
- `43s` `vercel deploy --prod --yes --name adb-qhvza-static-web --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" 2>&1 | tail -8`
- `46s` `V="npx -y vercel@latest" && $V link --yes --project adb-qhvza-static-web --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" 2>&1 | tail -3 && $V deploy --prod --yes --token "$VERCEL_TOKEN" --scope "$VE`
- `1m 11s` `ls -a; cat .gitignore; printf '.env\n.env.local\n.vercel\nnode_modules\ntest\ndeployment.json\n' > .vercelignore; npx -y vercel@latest deploy --prod --yes --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM`
- `1m 29s` `U=https://adb-qhvza-static-web.vercel.app`
- `1m 37s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v6/deployments?teamId=$VERCEL_TEAM_ID&app=adb-qhvza-static-web" | python3 -c "import json,sys;[print(d['uid'],d['url'],d['state`
- `1m 43s` `curl -s -XDELETE -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v13/deployments/dpl_HpQDu1PbN4iNc7tQ4xgTmdeqhF1b?teamId=$VERCEL_TEAM_ID"; echo`
