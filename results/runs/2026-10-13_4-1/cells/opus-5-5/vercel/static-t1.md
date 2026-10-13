# ✅ Static Content Site on Vercel with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-tibat-static-web.vercel.app (from deployment.json)
- Estimated hosting: $0.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium
- Resource prefix: `adb-tibat-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 25s | 1m 57s | 3m 22s |
| Turns | 9 | 7 | |
| Tokens | 211.0K | 208.6K | 419.6K |
| Agent cost | $0.29 | $0.13 | $0.42 |
| Shell commands | 8 | 6 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 395 lines in 15 files (JavaScript 192, HTML 166, CSS 37, JSON 32)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

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
| project | adb-tibat-static-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live at **https://adb-tibat-static-web.vercel.app**, and every requirement in `TASK.md` passed when tested through that URL.
>
> **What I deployed:** one Vercel project, `adb-tibat-static-web`, deployed with the Vercel CLI. It serves the three pages as static files and runs `/api/contact` as a Node.js serverless function. It should cost $0 a month, since this little traffic fits within the free allowances.
>
> **What I tested on the public URL:**
> - **Pages:** `/`, `/about` and `/contact` return 200 as `text/html`, with a title, the viewport meta tag, navigation and the right content. `/contact` has the `name`, `email` and `message` fields and a submit button.
> - **Unknown paths:** `/missing` returns 404, and `/about.html` redirects to `/about`.
> - **API:** valid input returns 200 with `{"ok":true}`. A missing name, a bad email, an empty message or malformed JSON each return 400 with a reason.
> - **Browser:** in a headless Chrome at phone width, submitting the form showed the confirmation without reloading the page, and nothing was wider than the screen.
>
> **Things to know:**
> - **Preview URLs are locked:** the public address above is open, but each deployment's own preview URL stays behind Vercel's login, which is the default setting.
> - **Odd error for non-JSON posts:** a POST without the JSON content type gets "Name is required" rather than "Invalid JSON body". The browser form always sends JSON, so users never see this.
> - **No secrets saved:** `.env` was not needed because I created no credentials. The token isn't in any file; the CLI's auto-created `.env.local` is gitignored and excluded from deploys.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty.

## Shell commands during deploy

- `2s` `(vercel --version || npx -y vercel@latest --version) 2>&1 | tail -2`
- `38s` `printf '.env\n.env*\ntest\ndeployment.json\nTASK.md\n' > .vercelignore && echo '.env' >> .gitignore && \`
- `59s` `npx -y vercel@latest deploy --prod --yes --scope "$VERCEL_TEAM_ID" --token "$VERCEL_TOKEN" 2>&1 | grep -v -i token | tail -40; cat .vercel/project.json`
- `1m 17s` `U=https://adb-tibat-static-web.vercel.app`
- `1m 27s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i playwright@latest >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1 && cat > t.mjs <<'EOF'`
- `1m 50s` `cat > deployment.json <<'EOF'`
