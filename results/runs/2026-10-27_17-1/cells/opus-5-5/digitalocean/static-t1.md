# ✅ Static Content Site on DigitalOcean with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-cqdoh-static-ve78h.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-cqdoh-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 40s | 2m 10s | 4m 47s |
| Turns | 12 | 7 | |
| Tokens | 455.3K | 360.6K | 1.09M |
| Agent cost | $0.50 | $0.15 | $0.84 |
| Shell commands | 11 | 6 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 57s, 278.2K tokens, $0.19).

## Screenshots

**The home page** (https://adb-cqdoh-static-ve78h.ondigitalocean.app/)

![The home page](static-t1/home.jpg)

**The contact page after the verifier submitted the form** (https://adb-cqdoh-static-ve78h.ondigitalocean.app/contact)

![The contact page after the verifier submitted the form](static-t1/contact.jpg)

## What was built

- Runtime: Node.js 22
- Frameworks: Node.js http module (built in)
- Packaging: Docker (node:22-alpine), App spec (.do/app.yaml)
- Hosting: App Platform service (apps-s-1vcpu-0.5gb), DigitalOcean Container Registry (starter)
- Code: 434 lines in 18 files (JavaScript 193, HTML 164, Shell 39, CSS 30, Markdown 24, JSON 24, YAML 15, Docker 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

### Stack fit

**84/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A Node.js server with no dependencies on an App Platform web service is a simple, well-reasoned fit for three pages and one API route. It gives up some platform fit by running a container for static content, and it deploys through a local Docker build rather than the buildpack STACK.md described.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 9/10 | The built-in `http` module serves exact clean paths, real 404s and a same-origin JSON endpoint with proper validation. That meets every requirement without needing a data store. |
| Proportion | 30 | 9/10 | There is one file of about 100 lines, no npm dependencies and tests that use node:test. It is minimal. The Dockerfile and registry add a small step beyond what a buildpack would need. |
| Platform fit | 30 | 7/10 | An always-on $5 container serves what is almost entirely static content, where App Platform's static site plus a Function or a small route could have used the CDN. STACK.md planned a buildpack deploy, but the build switched to a locally built Docker image in DOCR. The tradeoff is reasoned and works, though. |

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**87/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.27) of the process, the code, the hosting plan and the live app.

Northwind Robotics is built and deployed cleanly: a Node.js server with no dependencies, running as a non-root container on a paid App Platform service from a private DOCR registry. No secrets leaked, and only the intended routes are exposed. The remaining weaknesses are minor: the base image isn't pinned by digest, images are built locally rather than from a committed revision, the app sends no HSTS, CSP or frame-protection headers, and the contact endpoint has no rate limiting.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no runtime secrets. The DigitalOcean token was only read from the environment (deploy.sh sources .env, and .env is in .gitignore and .dockerignore), it never appeared in transcript output, and the agent checked that no dop_v1 token was written to any file. |
| Deployment provenance | 20 | 7/10 | The image was built locally from the agent's own sources, pushed to the owner's private DOCR registry, and deployed under a unique timestamped tag. The live spec matches the image tag that was pushed, and the app has no npm dependencies. However, the base image is the floating tag node:22-alpine with no digest, there is no source-control commit tying the image to its code, and a mutable `latest` tag is pushed as well. |
| Terms compliance | 15 | 9/10 | This is a commercial app, and paid App Platform services ($5 apps-s-1vcpu-0.5gb) and the DOCR starter tier are both allowed for commercial use under DigitalOcean's standard terms. The service is always on, with no sleep or expiry. The benchmark couldn't read the account plan, so this rests on DigitalOcean's general terms. |
| Least privilege | 15 | 9/10 | The container runs as the non-root `node` user, the deployment has no data stores, and only the single HTTP service is public. The registry is private. Pushing the extra mutable `latest` tag is the only minor excess. |
| Transport security | 10 | 7/10 | HTTP redirects to HTTPS with a 301, and the certificate is valid (Google Trust Services, expires Dec 2026). The app sets X-Content-Type-Options, but it sends no HSTS, CSP or frame-protection headers, even though the server code could easily have set them. |
| Attack surface | 10 | 10/10 | Only allowlisted routes are served. /.env, /.git/config, /server.js, /package.json, /Dockerfile, /.do/app.yaml and path-traversal attempts all return 404 or 400. There are no directory listings or stack traces, and /healthz returns only 'ok'. |
| Application security | 5 | 8/10 | Input is validated strictly by type and format, the request body is capped at 64 KB (413), non-POST methods return 405, and the client renders messages with textContent, so there's no XSS. The public contact endpoint has no rate limiting, but since submissions are neither stored nor emailed the impact is small. |

Findings:

- **low** · deployment · Base image not pinned by digest: app/Dockerfile:1 `FROM node:22-alpine` Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it on purpose.
- **low** · deployment · Image built from an uncommitted local tree and a mutable latest tag pushed: app/deploy.sh:14-16 builds locally and pushes both :$TAG and :latest; there is no git commit or CI build in process/build.md or deploy.md Fix: Build from a committed revision (for example a GitHub-linked App Platform source or CI), tag images with the commit SHA, and stop pushing `latest`.
- **low** · app · Missing HSTS, CSP and frame-protection headers: curl -sI https://adb-cqdoh-static-ve78h.ondigitalocean.app/ returns only x-content-type-options and cache-control as security-related headers; server.js:27 sets only X-Content-Type-Options Fix: Add Strict-Transport-Security, a restrictive Content-Security-Policy (default-src 'self'), and X-Frame-Options: DENY or frame-ancestors 'none' in send().
- **low** · app · No rate limiting on public contact endpoint: server.js:44-71 handleContact accepts unlimited POSTs; the only limit is the MAX_BODY of 64 KB Fix: Add a simple per-IP rate limit, or rely on the Cloudflare/App Platform edge, before the form is connected to email or storage.
- **info** · deployment · Single instance, no redundancy: process/resources.json: instance_count 1 on apps-s-1vcpu-0.5gb Fix: That's acceptable for a marketing site. Scale to 2 instances if uptime becomes critical.

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
| Light use | $5.00 | fixed monthly prices; 0.0373 GiB out of a 50 GiB allowance |
| Busy | $5.00 | fixed monthly prices; 49 GiB out of a 50 GiB allowance |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| app | adb-cqdoh-static | adb-cqdoh-static-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-cqdoh-static-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-cqdoh-static | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The site is live at **https://adb-cqdoh-static-ve78h.ondigitalocean.app**, and every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What's deployed:**
> - **App Platform app `adb-cqdoh-static`** (id `2badda0c-2351-4f3c-acbc-91c18306d2b0`): one web service, `adb-cqdoh-static-web`, on the smallest size (`apps-s-1vcpu-0.5gb`) in the nyc region, at $5/month. HTTPS comes with the default `ondigitalocean.app` address.
> - **Container registry `adb-cqdoh-static`**: free starter plan in nyc3. It holds the app's Docker image.
> - **Estimated cost:** $5/month.
>
> **Testing through the public URL:**
> - `/`, `/about` and `/contact` return 200 with `text/html`, and an unknown path returns 404.
> - `POST /api/contact` returns 200 with `{"ok":true}` for valid input. It returns 400 with an error message for a missing name, a bad email or an empty message.
> - The contact page has the `name`, `email` and `message` fields, a submit button, a title and the viewport tag.
> - In headless Chrome at phone width, the form showed its confirmation without reloading the page, and nothing scrolled sideways.
>
> The first deploy attempt failed because App Platform read the image tag as a number; I fixed `deploy.sh` to quote it. The site runs on a single instance, so there's no backup instance if it goes down.
>
> To redeploy, run `./deploy.sh`, then check with `./smoke.sh <url>`. No steps needed a person, so `human_steps` in `deployment.json` is empty. The token was only read from the environment and isn't stored in any file.

## Shell commands during deploy

- `3s` `which doctl || echo none; doctl account get --format Email,Status,DropletLimit 2>&1 | tail -1 | sed 's/^[^ ]*@/***@/'; doctl registry get 2>&1 | tail -2; doctl apps list 2>&1 | head`
- `8s` `./deploy.sh 2>&1 | grep -vE '^\s*$' | tail -25`
- `59s` `sed -i 's/s\/tag: latest\/tag: \$TAG\//s\/tag: latest\/tag: \\"$TAG\\"\//' deploy.sh && grep -n 'sed "s' deploy.sh && ./deploy.sh 2>&1 | grep -vE 'Waiting|exists|Pushed|Preparing|^\s*$|#' | tail -15`
- `1m 45s` `U=https://adb-cqdoh-static-ve78h.ondigitalocean.app; ./smoke.sh $U; curl -s $U/contact | grep -oE 'name="(name|email|message)"|<textarea|type="submit"|<title>[^<]*|name="viewport"' ; sed -i "s#http://`
- `1m 56s` `doctl registry options subscription-tiers >/dev/null; doctl registry get -o json | python3 -c 'import json,sys;d=json.load(sys.stdin);d=d[0] if isinstance(d,list) else d;print(d.get("name"),d.get("reg`
- `2m 04s` `cat > deployment.json <<'EOF'`
