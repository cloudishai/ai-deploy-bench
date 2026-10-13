# ✅ Static Content Site on DigitalOcean with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-nzg8i-static-kk63g.ondigitalocean.app (from deployment.json)
- Estimated hosting: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-nzg8i-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 26s | 2m 18s | 3m 44s |
| Turns | 7 | 9 | |
| Tokens | 255.8K | 390.8K | 646.6K |
| Agent cost | $0.31 | $0.17 | $0.48 |
| Shell commands | 6 | 8 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 392 lines in 15 files (JavaScript 192, HTML 156, CSS 36, JSON 25, YAML 16, Docker 8, Markdown 7)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.25) of the process, the code and the live app.

The deployment is a small zero-dependency Node.js server, running as non-root on DigitalOcean App Platform from a private DOCR image. It has a tight route allowlist, so nothing beyond the app is exposed, and no secrets are involved. The main weaknesses are missing security headers (HSTS, CSP, frame protection), no rate limiting or field length caps on the public contact endpoint, user input written unsanitized to logs, and build inputs referenced by mutable tags rather than pinned digests.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets and none are in the source, image or deployed files. The DO token was only used through the $DIGITALOCEAN_ACCESS_TOKEN env var and `doctl registry login`. One small point: the deploy transcript printed account metadata (owner email, team UUID) into the logs. |
| Deployment provenance | 15 | 7/10 | The image was built from the reviewed source and pushed to a registry the owner controls. The app has no npm dependencies. But the base image `node:22-alpine` isn't pinned to a digest, the app references the mutable tag `v1`, and doctl was downloaded and installed without checksum verification. |
| Transport security | 15 | 6/10 | HTTPS works with a valid Google Trust Services certificate, and HTTP redirects to HTTPS with a 301. X-Content-Type-Options is set, but HSTS, Content-Security-Policy and frame protection (X-Frame-Options or frame-ancestors) are all missing. |
| Attack surface | 15 | 10/10 | The server uses an explicit allowlist of routes, served from memory, so source files, .env, .git and the Dockerfile all return 404 and traversal attempts return 400. There are no directory listings or stack traces, and the only extra endpoint is a benign /healthz. |
| Application security | 20 | 7/10 | Input validation is solid: it checks types, the body is capped at 64KB, and JSON parse errors are handled. The client uses textContent, so there is no XSS. However, the public POST endpoint has no rate limiting and no per-field length limits, and unsanitized names and emails go into logs, which allows log forging. |
| Least privilege | 10 | 9/10 | The container runs as the non-root `node` user from a minimal Alpine image. The app has no data stores, one small instance and a private DOCR registry. Nothing is needlessly public. |

Findings:

- **medium** · Missing HSTS, CSP and frame-protection headers: curl -sI https://adb-nzg8i-static-kk63g.ondigitalocean.app/ returns only x-content-type-options: nosniff, with no strict-transport-security, content-security-policy or x-frame-options. app/server.js:21-28 sets only X-Content-Type-Options. Fix: Add Strict-Transport-Security (max-age=31536000; includeSubDomains), a restrictive Content-Security-Policy (default-src 'self'; frame-ancestors 'none'), X-Frame-Options: DENY and Referrer-Policy in send().
- **low** · No rate limiting or field length limits on public contact endpoint: app/server.js:44-70 handleContact accepts any number of requests, and each field can be up to the 64KB body limit (MAX_BODY, line 13). No throttling exists in the code or in the App Platform spec (app/app.yaml). Fix: Add per-IP rate limiting (in-app token bucket or a Cloudflare/edge rule) and cap the name, email and message lengths, for example 100, 254 and 5000 characters.
- **low** · Unsanitized user input written to logs (log forging, PII in logs): app/server.js:67 console.log(`Contact submission from ${data.name.trim()} <${data.email.trim()}>`). The name can contain CR/LF characters, which inject fake log lines, and email addresses are stored in the platform logs. Fix: Strip control characters or JSON-encode logged values, and consider not logging the email address.
- **low** · Base image and deployed image referenced by mutable tags: app/Dockerfile:1 FROM node:22-alpine (no digest). app/app.yaml:8 tag: v1 rather than the pushed digest sha256:5dc6a0b2... (process/deploy.md). Fix: Pin the base image with node:22-alpine@sha256:<digest>, and deploy by image digest or immutable unique tags.
- **low** · doctl installer downloaded without checksum verification: process/deploy.md: curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ Fix: Verify the release against its published sha256 checksums file before installing.
- **info** · Account metadata printed to deploy logs: process/deploy.md first command: curl ... https://api.digitalocean.com/v2/account | head -c 400, which printed the account email and team UUID. The token itself was passed through an environment variable and not echoed. Fix: Don't dump account details to logs. Use `doctl account get --format Status` or similar to check auth.

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
| app | adb-nzg8i-static | adb-nzg8i-static-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-nzg8i-static-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-nzg8i-static | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The site is live at **https://adb-nzg8i-static-kk63g.ondigitalocean.app**, and every requirement in `TASK.md` works through that URL. Nothing needed a person, so `human_steps` is empty.
>
> **What I deployed:**
> - **Container registry** `adb-nzg8i-static`: a DigitalOcean registry on the free Starter tier, holding the image `adb-nzg8i-static-web:v1`.
> - **App Platform app** `adb-nzg8i-static`: runs that image as one web service on the smallest paid size (`apps-s-1vcpu-0.5gb`) in New York. It gets HTTPS automatically, and plain HTTP redirects to HTTPS. The app's configuration is in `app.yaml`.
> - **Cost:** about $5/month, all of it for the web service; the registry is free.
>
> App Platform's free static-site option needs a connected GitHub repository, and none is linked to this account. That's why I built a Docker image and ran it as a paid service instead.
>
> **What I tested on the public URL:**
> - `/`, `/about` and `/contact` return 200 as HTML.
> - Unknown paths, including `/about.html`, return 404.
> - `POST /api/contact` returns 200 for valid input. A missing name, a bad email or an empty message each return 400 with an error message.
> - In a headless Chrome browser, filling in and sending the contact form showed the confirmation without a page reload.
>
> No credentials were created, so there is no `.env` file. The details are recorded in `deployment.json`.

## Shell commands during deploy

- `5s` `which doctl; doctl version 2>/dev/null; curl -s -H "Authorization: Bearer $DIGITALOCEAN_ACCESS_TOKEN" https://api.digitalocean.com/v2/registry; echo; curl -s -H "Authorization: Bearer $DIGITALOCEAN_AC`
- `10s` `cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ && doctl version && doctl registry creat`
- `29s` ❌ `doctl registry login >/dev/null && IMG=registry.digitalocean.com/adb-nzg8i-static/adb-nzg8i-static-web:v1 && docker build -q --platform linux/amd64 -t $IMG . && docker push -q $IMG && cat > app.yaml <`
- `1m 29s` ❌ `doctl apps list --format ID,Spec.Name,DefaultIngress,ActiveDeployment.Phase`
- `1m 32s` `doctl apps list -o json | python3 -c "import json,sys;[print(a['id'],a['spec']['name'],a.get('live_url'),a.get('active_deployment',{}).get('phase')) for a in json.load(sys.stdin)]"`
- `1m 37s` `U=https://adb-nzg8i-static-kk63g.ondigitalocean.app`
- `1m 45s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i -s playwright >/dev/null 2>&1 && npx playwright install --with-deps chromium >/dev/null 2>&1; cat > t.js <<'EOF'`
- `2m 12s` `cat > deployment.json <<'EOF'`
