# ✅ Static Content Site on Railway with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-yz0s2-static-web-production.up.railway.app (from deployment.json)
- Estimated hosting: Light use: $5.28/month, Busy: $27.63/month (the agent estimated $1.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-yz0s2-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 00s | 2m 17s | 4m 56s |
| Turns | 13 | 7 | |
| Tokens | 500.4K | 353.2K | 1.13M |
| Agent cost | $0.52 | $0.15 | $0.81 |
| Shell commands | 12 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 39s, 273.5K tokens, $0.13).

## Screenshots

**The home page** (https://adb-yz0s2-static-web-production.up.railway.app/)

![The home page](static-t1/home.jpg)

**The contact page after the verifier submitted the form** (https://adb-yz0s2-static-web-production.up.railway.app/contact)

![The contact page after the verifier submitted the form](static-t1/contact.jpg)

## What was built

- Runtime: Node.js 18+
- Frameworks: Node.js http module (built in)
- Packaging: railway.json
- Code: 418 lines in 16 files (JavaScript 208, HTML 166, JSON 36, CSS 33, Markdown 26, Shell 11)
- Dependencies: 0 npm, 0 Python
- Deploy config: `railway.json`

### Stack fit

**90/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A dependency-free Node.js server on a single Railway service fits a three-page site with one same-origin form endpoint well. STACK.md explains the choice soundly, and the build matches it.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | Node's built-in http module serves exact extensionless routes, real 404s and a validated JSON endpoint on the same origin, which covers everything TASK.md asks for, and the app needs no data store. |
| Proportion | 30 | 10/10 | It is one roughly 100-line file with zero dependencies and no build step, using the built-in node:test runner, which is about as small as these requirements allow. |
| Platform fit | 30 | 8/10 | Railway has no static-only hosting or functions, so one small always-on service serving both pages and the API is the natural fit there, and it costs about $1/month. Static files are served from a container, which is acceptable on this platform. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): resources: paid resources: adb-yz0s2-static

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.25) of the process, the code, the hosting plan and the live app.

The Northwind Robotics site is a small, dependency-free Node server deployed cleanly to Railway with no secrets involved. HTTPS is enforced with a valid certificate and only allowlisted paths are exposed. The remaining weaknesses are minor: no security headers, an unpinned Node runtime and Railpack base image, a local `railway up` upload with no source repository, a likely root container, and no rate limiting on the contact form.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no secrets. The Railway token came only from the environment, was never echoed (the transcript shows only 'token set'), and .env is excluded by .gitignore and .railwayignore. No credentials show up in source, logs or deployed files. |
| Deployment provenance | 20 | 7/10 | Local source was uploaded with `railway up`, built by Railpack and checked live, and there are no npm dependencies. Two inputs are not pinned: the Node version (engines '>=18', so Railpack picked Node 24) and the Railpack base image chosen by the platform. There is also no source repository behind the deployed artifact. |
| Terms compliance | 15 | 7/10 | This is a commercial app on what the agent describes as the account's existing usage-based Railway plan. Railway's paid plans allow commercial use and do not sleep services, but context.json does not name the plan, so I can't confirm the account isn't on the trial/free tier, which has credit limits. Separately, railway.json config-as-code is deprecated after 2026-12-01. |
| Least privilege | 15 | 7/10 | There is a single service with no data store, volume or extra public resources, and only the needed HTTP port is exposed. The Railpack image runs as its default (root) user, and the agent took no steps to drop privileges. |
| Transport security | 10 | 7/10 | HTTPS works with a valid Let's Encrypt certificate, and HTTP returns a 301 to HTTPS. The app sets none of HSTS, X-Content-Type-Options, frame protection or CSP, even though it fully controls its response headers. |
| Attack surface | 10 | 9/10 | Routing uses an exact-path allowlist, so .env, .git, server.js, package.json, *.html and traversal attempts all return 404, with no listings or stack traces. The only extra endpoint is a harmless /healthz. |
| Application security | 5 | 8/10 | The contact endpoint checks types, required fields and email format, limits bodies to 64 KB (returns 413), handles bad JSON cleanly, and the client renders responses with textContent, so there is no XSS. There is no rate limiting or bot protection on the public form, and submitter emails are written to the logs. |

Findings:

- **low** · app · No security headers set: curl -sI https://adb-yz0s2-static-web-production.up.railway.app/ returns only content-type, date, server, x-railway-* and content-length; there is no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. server.js:83-98 writes only Content-Type and Content-Length. Fix: Add HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY (or CSP frame-ancestors 'none') and a strict CSP such as default-src 'self' to every response in server.js.
- **low** · deployment · Node runtime and build base image not pinned: app/package.json engines {"node": ">=18"}; deployment.json reports Node.js 24 picked by Railpack; railway.json uses builder RAILPACK with no pinned image or version. Fix: Pin an exact Node major/minor (engines or .node-version / RAILPACK_NODE_VERSION), or deploy from a Dockerfile with a digest-pinned base image.
- **low** · deployment · Deployed from an untracked local upload: deploy.md: `railway up --service adb-yz0s2-static-web --ci`; deployment.json notes 'no GitHub repo, no container registry'. Fix: Deploy from a version-controlled repository the owner controls (for example Railway's GitHub integration), so every deployment maps to a commit.
- **low** · deployment · Container likely runs as root: railway.json uses the default Railpack build with no user configuration; Railpack images run as root by default, and the build log shows apt/libc-bin steps in the image. Fix: Use a Dockerfile with a non-root USER (for example node), or configure the build to drop root privileges.
- **low** · app · Contact endpoint has no rate limiting: server.js:46-70 accepts every valid POST /api/contact; a POST of {"name":"<script>","email":"a@b.co","message":"hi"} returned 200 {"ok":true}, and no throttling exists. Fix: Add a simple per-IP rate limit and/or a honeypot field before submissions are ever stored or emailed.
- **info** · app · Submitter email addresses logged: server.js:67 console.log(`Contact form submission from ${data.email.trim()}`) Fix: Avoid logging personal data, or mask it and document log retention.
- **info** · deployment · Plan not verifiable; config format deprecated: process/context.json has an empty account object; deployment.json says "account's existing Railway plan (usage-based)" and notes that railway.json is deprecated after 2026-12-01. Fix: Confirm the account is on a paid Hobby or Pro plan (not the trial) for commercial uptime, and run `railway config migrate` before 2026-12-01.

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
| Light use | $5.28 | memory billed all month, CPU for ~10 h of activity, 0.04 GB egress at $0.05/GB |
| Busy | $27.63 | memory billed all month, CPU for ~730 h of activity, 52.6 GB egress at $0.05/GB |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-yz0s2-static | 1 service(s) | $25.00 | 1 service(s) at the assumed 1 vCPU / 0.5 GB each, always on; usage is metered per second so a mostly idle service costs less than this list price |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live at **https://adb-yz0s2-static-web-production.up.railway.app**, and every requirement in `TASK.md` works through that address.
>
> **What I deployed**
> - A Railway project `adb-yz0s2-static` with one web service, `adb-yz0s2-static-web`, in the production environment.
> - I uploaded the code straight from this directory with `railway up`, so no GitHub repo or image registry was involved. The service has a Railway-provided HTTPS address and a health check on `/healthz`.
> - Estimated cost is about $1/month, which the plan's included usage should cover.
>
> **What I tested through the public address**
> - **Pages:** `/`, `/about` and `/contact` return 200 as HTML, each with the required heading or form fields.
> - **404s:** unknown paths and `.html` suffixes (e.g. `/about.html`) return 404.
> - **Form endpoint:** `POST /api/contact` returns 200 `{"ok":true}` for valid input. A missing name, invalid email or empty message each return 400 with a reason.
> - **HTTPS:** plain HTTP redirects to HTTPS.
> - **Browser:** in headless Chromium at phone width, the form showed its confirmation without reloading the page, and an invalid email showed the error message.
>
> **Things to know**
> - **Config format:** Railway now flags `railway.json` as deprecated. It keeps working until 2026-12-01; running `railway config migrate` before then moves it to the new format.
> - **Credentials:** I used only the token you provided and created none, so there is no `.env` and `human_steps` in `deployment.json` is empty.
>
> `deploy.sh` and the `.railwayignore` from earlier are still in the directory. I didn't run the script, since I did the same steps by hand.

## Shell commands during deploy

- `4s` `test -n "$RAILWAY_API_TOKEN" && echo token set; which railway || npm i -g @railway/cli >/dev/null 2>&1; railway whoami 2>&1 | head -3; railway list 2>&1 | head`
- `9s` `railway init --name adb-yz0s2-static --json 2>&1 | tail -5; railway add --service adb-yz0s2-static-web --json 2>&1 | tail -5`
- `13s` `railway up --service adb-yz0s2-static-web --ci 2>&1 | tail -15`
- `1m 46s` `railway domain --service adb-yz0s2-static-web --json 2>&1 | tail -3; railway status --json 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);e=d['environments']['edges'][0]['node'];prin`
- `1m 54s` `U=https://adb-yz0s2-static-web-production.up.railway.app; for i in $(seq 1 30); do [ "$(curl -s -o /dev/null -w '%{http_code}' $U/)" = 200 ] && break; sleep 5; done`
- `2m 09s` `cat > deployment.json <<'EOF'`
