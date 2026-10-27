# ✅ Static Content Site on Vercel with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-t25sv-static-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-t25sv-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 43s | 45s | 4m 14s |
| Turns | 12 | 5 | |
| Tokens | 459.7K | 316.4K | 1.72M |
| Agent cost | $0.51 | $0.14 | $1.05 |
| Shell commands | 11 | 4 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 47s, 945.6K tokens, $0.40).

## Screenshots

**The home page** (https://adb-t25sv-static-web.vercel.app/)

![The home page](static-t1/home.jpg)

**The contact page after the verifier submitted the form** (https://adb-t25sv-static-web.vercel.app/contact)

![The contact page after the verifier submitted the form](static-t1/contact.jpg)

## What was built

- Runtime: Node.js 18+
- Frameworks: Plain Vercel Functions
- Packaging: vercel.json
- Hosting: Vercel project, Vercel Functions
- Code: 392 lines in 16 files (JavaScript 190, HTML 166, CSS 36, JSON 32, Markdown 19)
- Dependencies: 0 npm, 0 Python
- Deploy config: `vercel.json`

### Stack fit

**97/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Static files on Vercel's CDN plus one zero-dependency Node function is about the simplest stack that meets every requirement, and it matches what Vercel does best. STACK.md weighs the alternatives sensibly and the build follows it.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 10/10 | Plain HTML/CSS served from Vercel's CDN suits static pages. cleanUrls and 404.html give exact paths and real 404s, and a small Node function handles the JSON validation endpoint. No data store is needed. |
| Proportion | 30 | 9/10 | There is no framework, build step or runtime dependency, as STACK.md planned. The only extra is a small local dev-server.js, which isn't deployed. |
| Platform fit | 30 | 10/10 | The stack uses Vercel's native primitives (CDN static output, zero-config api/ functions, cleanUrls, custom 404) rather than routing static pages through a server. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**76/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.34) of the process, the code, the hosting plan and the live app.

The deployment is a clean, zero-dependency static site plus one Vercel Function. Secrets were handled well, nothing beyond the app is exposed, and it is served only over HTTPS with HSTS. The main problem is compliance: a commercial business site sits on a Vercel Hobby plan, whose terms are for non-commercial use only, and the agent didn't flag it. Smaller gaps are missing app-set security headers, no length or rate limits on the contact endpoint, and a leftover anonymous temporary deployment.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | VERCEL_TOKEN and team ID came from environment variables and were never printed or written into source. The CLI-downloaded OIDC token in .env.local was excluded by .vercelignore and isn't served. The app needs no secrets of its own. |
| Deployment provenance | 20 | 8/10 | Production runs the reviewed zero-dependency static files and function, deployed by CLI from the local workspace into the owner's team with no build step or third-party packages. Two gaps: the deploy isn't tied to a commit, and an earlier attempt left an anonymous, unclaimed *.tmp.now copy of the app outside the owner's control. |
| Terms compliance | 15 | 2/10 | This is a business's marketing site (use: commercial), but it is hosted on a Vercel Hobby team. Vercel's Hobby terms limit the plan to personal, non-commercial use. The agent called it the 'team's existing plan' and never raised the conflict or the need for Pro. |
| Least privilege | 15 | 9/10 | There are only CDN static files and one stateless function, with no data stores or extra services. Vercel Authentication protects per-deployment URLs and only the production alias is public. Static responses carry the platform default Access-Control-Allow-Origin: *, which is harmless for public content. |
| Transport security | 10 | 8/10 | The site is HTTPS-only with a valid certificate. HTTP returns 308 to HTTPS and HSTS is set with preload. The agent didn't add X-Content-Type-Options, frame protection or a CSP, though vercel.json 'headers' could have set them. |
| Attack surface | 10 | 10/10 | Source files, .env, .env.local, .git, .vercel, package.json, tests and dev-server.js all return 404. /_src redirects to a Vercel login. Errors are generic JSON or the custom 404 page, with no stack traces. |
| Application security | 5 | 7/10 | Validation is correct and type-checked, and the client renders messages with textContent, so there is no XSS. The endpoint has no field length limits (a 2 MB message was accepted) and no rate limiting or bot protection. Impact is low because nothing is stored or sent. |

Findings:

- **high** · deployment · Commercial site hosted on a Vercel Hobby (non-commercial) plan: process/context.json: use=commercial, team_plans.team_U2tHOV4fpUx18nl9EpcRQ4hO=hobby. app/deployment.json: plan 'Team's existing plan; usage is well within free-tier limits'. The deploy transcript's final message says 'the team keeps its current plan' and never mentions the commercial-use restriction. Fix: Move the project to a Vercel Pro (or Enterprise) team before using it for the business, or tell the owner this is required and add it to human_steps.
- **low** · deployment · Unclaimed anonymous temporary deployment left running: process/deploy.md, final message: 'The temporary no-login deployment from the previous attempt was never claimed and will expire by itself'. The test script was rewritten from https://zippy-zither-43gb383.tmp.now. Fix: Deploy only into accounts the owner controls, and delete or claim any temporary copies right away instead of waiting for them to expire.
- **low** · deployment · Production deploy not tied to version-controlled source: process/deploy.md: 'vercel deploy --prod --yes --token "$VERCEL_TOKEN"' uploaded the local working directory. No git commit or repository is linked. Fix: Deploy from a git repository the owner controls (Vercel Git integration or CI deploying a tagged commit) so production maps to a known revision.
- **low** · app · Missing security headers the app could set: curl -sI https://adb-t25sv-static-web.vercel.app/ returns strict-transport-security only. There is no x-content-type-options, x-frame-options/frame-ancestors or content-security-policy. app/vercel.json has no 'headers' block. Fix: Add a vercel.json 'headers' rule for all paths with X-Content-Type-Options: nosniff, a CSP with default-src 'self' and frame-ancestors 'none', and Referrer-Policy.
- **low** · app · No size limits or abuse protection on /api/contact: POST /api/contact with a ~2 MB JSON message returned 200 {"ok":true}. lib/validate.js checks only non-empty strings. Repeated posts aren't throttled. The 1e5 limit in api/contact.js:19 never applies on Vercel because req.body is pre-parsed. Fix: Enforce maximum lengths (for example name 200, email 254, message 5000) and add rate limiting or Vercel Firewall/BotID rules before the endpoint is wired to email or storage.
- **info** · platform · Wildcard CORS on static assets: curl -sI https://adb-t25sv-static-web.vercel.app/ returns access-control-allow-origin: *. This is Vercel's default for static files, and the API response doesn't send it. Fix: No action needed for public marketing content.
- **info** · deployment · CLI wrote an OIDC token to .env.local in the workspace: process/deploy.md: 'vercel link' printed 'Downloading a fresh VERCEL_OIDC_TOKEN ... Created .env.local'. app/.vercelignore lists .env.* and a GET on /.env.local returns 404. Fix: Delete .env.local after deploying, since the app doesn't use the OIDC token.

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

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $0.00 of usage |
| Busy | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $5.75 of usage |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-t25sv-static-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live and public at **https://adb-t25sv-static-web.vercel.app**, and every requirement in `TASK.md` works through that URL.
>
> **What's deployed:** one Vercel project, `adb-t25sv-static-web` (ID `prj_tzVaitaAlGBu38sdZ12zOOnIpHHd`), in the team you provided. The three pages are served as static files, and `POST /api/contact` runs as a Node.js Vercel Function. It should cost $0 a month: the team keeps its current plan and this traffic is far below the free limits.
>
> **Tested through the public URL:**
> - `/`, `/about` and `/contact` return 200 `text/html`, each with a title, the viewport tag and navigation.
> - `/missing` returns 404.
> - `POST /api/contact` returns 200 `{"ok":true}` for valid input. It returns 400 with an error message for a missing name, a bad email, an empty message and malformed JSON.
> - In headless Chromium, submitting the form showed the confirmation without a page reload.
>
> **Things to know:**
> - The per-deployment links (`*-ai-deploy-bench.vercel.app`) ask for a Vercel login, because Vercel's default deployment protection is on. The production URL above is open to everyone.
> - The temporary no-login deployment from the previous attempt was never claimed and will expire by itself.
> - I didn't create any new credentials. The CLI wrote its own short-lived token to `.env.local` and its project link to `.vercel/`; both are kept out of git and out of the deployment.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty.

## Shell commands during deploy

- `4s` `[ -n "$VERCEL_TOKEN" ] && [ -n "$VERCEL_TEAM_ID" ] && echo creds-set; rm -rf .vercel; vercel --version; vercel whoami --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" 2>&1 | tail -2`
- `8s` `vercel link --yes --project adb-t25sv-static-web --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" 2>&1 | tail -3 && vercel deploy --prod --yes --token "$VERCEL_TOKEN" --scope "$VERCEL_TEAM_ID" > /tmp`
- `27s` `U=https://adb-t25sv-static-web.vercel.app`
- `39s` `printf '# No credentials were created; VERCEL_TOKEN / VERCEL_TEAM_ID come from the environment.\n' > .env && cat > deployment.json <<'EOF'`
