# ✅ Static Content Site on Render with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-81too-static-web.onrender.com (from deployment.json)
- Estimated hosting: $0.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-81too-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 20s | 2m 44s | 4m 05s |
| Turns | 8 | 15 | |
| Tokens | 297.2K | 866.2K | 1.16M |
| Agent cost | $0.32 | $0.49 | $0.81 |
| Shell commands | 7 | 13 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 417 lines in 15 files (JavaScript 193, HTML 174, CSS 37, JSON 23, Shell 13, YAML 8, Markdown 6)
- Dependencies: 0 npm, 0 Python
- Deploy config: `render.yaml`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optionally push this project to a GitHub/GitLab repo and connect it to Render (or recreate the service from render.yaml 

## Security review

**74/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.27) of the process, the code and the live app.

The Northwind Robotics site is a small, zero-dependency Node server. Its routing is tight, its contact endpoint validates input well, and no secrets were exposed. HTTPS is enforced with a redirect. The main weaknesses are no security headers at all (no HSTS, CSP, nosniff or frame protection), and a deployment that eval's app source packed into env vars on an unpinned public node:24-alpine image running as root, rather than building from a repo the owner controls.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets, none are in the source or deployed files, and the agent masked env output (sed 's/=.*/=***/') when it inspected the environment. RENDER_API_KEY was only passed by variable reference. The one small issue is that the transcript printed the Render owner's email address. |
| Deployment provenance | 15 | 4/10 | Production does not run a build from an owner-controlled repo. The app source is base64-packed into the APP_FILES env var and started with `node -e eval(...BOOT...)` on the unpinned public tag node:24-alpine. render.yaml describes a different (native Node runtime) setup from what is actually deployed. On the plus side, the app has zero npm dependencies. |
| Transport security | 15 | 6/10 | HTTPS works with a valid certificate and HTTP 301-redirects to HTTPS. However, the app sets no security headers at all: no HSTS, X-Content-Type-Options, frame protection or CSP. |
| Attack surface | 15 | 9/10 | An explicit allowlist router serves only the pages and two assets. /.env, /.git/config, /server.js, /package.json and /index.html all return 404, and there are no stack traces or debug endpoints. Only a trivial /healthz is exposed. |
| Application security | 20 | 8/10 | Input is validated well: types, an email regex, length limits, a 64 KB body cap and JSON parse errors handled. The client uses textContent, so there is no XSS. There is no rate limiting, though, the Content-Type is not enforced (cross-origin text/plain posts are accepted), and submitter names and emails are logged without sanitising them. |
| Least privilege | 10 | 7/10 | There is a single free web service with no data stores and no extra resources. But the container runs as root, which is the default for the node image because the dockerCommand never switches to the `node` user. |

Findings:

- **medium** · Source delivered via env vars and eval, not a controlled build: process/deploy.md line 163: dockerCommand "node -e eval(Buffer.from(process.env.BOOT,process.env.ENC).toString())" with APP_FILES/BOOT env vars; app/deploy/boot.js; app/render.yaml declares runtime: node, which does not match the deployed image service Fix: Deploy from a Git repo the owner controls (or a built image in a private registry) so that what runs is traceable to a commit, and keep render.yaml in line with the real service.
- **medium** · Base image pinned only by mutable tag: process/resources.json: source docker.io/library/node:24-alpine (no digest) Fix: Pin the base image by digest (node:24-alpine@sha256:...) and update it on purpose.
- **medium** · No security headers: curl -sI https://adb-81too-static-web.onrender.com/ returns only content-type, cache-control and CDN headers. There is no Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy; app/server.js:21-23 sets none of them Fix: Add HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY (or frame-ancestors 'none'), a restrictive CSP (default-src 'self') and Referrer-Policy in send().
- **low** · No rate limiting and Content-Type not enforced on /api/contact: POST /api/contact with Origin: https://evil.example and Content-Type: text/plain returned HTTP 200 {"ok":true}; app/server.js:40-69 has no throttling Fix: Require application/json (which forces a CORS preflight for cross-origin calls) and add per-IP rate limiting or a honeypot/CAPTCHA.
- **low** · Unsanitised PII written to logs: app/server.js:66 logs `Contact submission from ${name} <${email}>`; only the ends are trimmed, so embedded newlines can forge log lines Fix: Avoid logging PII, or JSON-encode or escape logged values.
- **low** · Container runs as root: The node:24-alpine default user is root, and the dockerCommand (process/deploy.md line 163) does not drop privileges Fix: Run as the image's `node` user (a custom Dockerfile with USER node).
- **info** · Account email echoed in transcript: process/deploy.md: the /v1/owners response printed the owner email Fix: Filter API responses to the fields you need (for example jq '.[].owner.id').
- **info** · Attack surface limited to allowlisted routes: /.env, /.git/config, /server.js, /package.json, /public/index.html -> 404; /..%2fserver.js -> 400; unknown path -> custom 404 page Fix: None.

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
| service | adb-81too-static-web | free | $0.00 | free x 1 instance(s) |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live at **https://adb-81too-static-web.onrender.com**, and every requirement in `TASK.md` works through that URL.
>
> **What's deployed:** one Render web service, `adb-81too-static-web` (`srv-db79ia67bikc73a1jtqg`), on the free plan in Oregon. Cost is $0/month. Free services go to sleep when idle, so the first visit after about 15 minutes can take up to a minute to load.
>
> **How it gets the code:** Render normally builds from a connected GitHub or GitLab repo, and there were no credentials for one. It also has no way to upload local files. So the service runs Node's official public image (`node:24-alpine`) and receives the app's files through environment variables. A small startup script (`deploy/boot.js`) writes them out and starts the server. Pulling that standard image is the only thing used from outside Render; nothing of ours is hosted anywhere else. The first deploy failed because of how Render runs the start command; the second one fixed that.
>
> **What I tested through the public URL:**
> - `/`, `/about` and `/contact` return 200 as `text/html`. Each has a title, the viewport tag, the right heading, links to the other pages and the form fields.
> - Unknown paths, including `/about.html`, return 404.
> - `POST /api/contact` returns 200 `{"ok":true}` for valid input. A missing name, a bad email or an empty message each return 400 with an error message.
> - In a headless Chrome browser, submitting the form showed the confirmation without reloading the page.
>
> **Files added:**
> - `deployment.json`
> - `deploy/boot.js`: the startup script.
> - `deploy/redeploy.sh`: pushes the current code and starts a new deploy. It needs `RENDER_API_KEY`.
>
> I created no credentials, so there is no `.env`. The one item under `human_steps` is optional and doesn't block anything: connect a Git repo to Render, which would allow normal builds and automatic deploys on each push.

## Shell commands during deploy

- `4s` `gh auth status 2>&1 | head -5; env | grep -iE "github|git_|token" | sed 's/=.*/=***/' ; curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/owners | head -c 600; echo; curl -s`
- `24s` `tar czf - package.json server.js public | base64 -w0 | wc -c`
- `31s` `B64=$(tar czf - package.json server.js public | base64 -w0) && jq -n --arg b "$B64" '{`
- `36s` `for i in $(seq 1 40); do s=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/srv-db79ia67bikc73a1jtqg/deploys/dep-db79ia67bikc73a1jukg | jq -r .status); echo $s; `
- `55s` `curl -s -G -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/logs --data-urlencode ownerId=tea-db6fig0473hc73eb9aeg --data-urlencode resource=srv-db79ia67bikc73a1jtqg --data-urlenco`
- `1m 12s` `mkdir -p /tmp/boot && cat > /tmp/boot/boot.js <<'EOF'`
- `1m 20s` ❌ `cat > /tmp/boot/boot.js <<'EOF'`
- `1m 27s` ❌ `pgrep -f "server.js" >/dev/null && pkill -f "node server.js"; S=srv-db79ia67bikc73a1jtqg; H=(-H "Authorization: Bearer $RENDER_API_KEY" -H "Content-Type: application/json")`
- `1m 31s` `S=srv-db79ia67bikc73a1jtqg; H=(-H "Authorization: Bearer $RENDER_API_KEY" -H "Content-Type: application/json")`
- `1m 38s` `S=srv-db79ia67bikc73a1jtqg; H=(-H "Authorization: Bearer $RENDER_API_KEY" -H "Content-Type: application/json")`
- `2m 00s` `U=https://adb-81too-static-web.onrender.com`
- `2m 08s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i playwright@1 >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1; cat > t.js <<'EOF'`
- `2m 36s` `mkdir -p deploy && cp /tmp/boot/boot.js deploy/boot.js && cat > deploy/redeploy.sh <<'EOF'`
