# ✅ Data / Visualization App on DigitalOcean with Opus 5.5 (trial 1)

**success**: 12/12 checks passed (100%).

- URL: https://adb-6mbv0-dataviz-dyatk.ondigitalocean.app (from deployment.json)
- Estimated hosting: Light use: $5.00/month, Busy: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-6mbv0-dataviz`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 36s | 1m 26s | 4m 01s |
| Turns | 16 | 9 | |
| Tokens | 578.9K | 510.4K | 1.09M |
| Agent cost | $0.54 | $0.19 | $0.73 |
| Shell commands | 11 | 7 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The dashboard** (https://adb-6mbv0-dataviz-dyatk.ondigitalocean.app/)

![The dashboard](dataviz-t1/dashboard.jpg)

## What was built

- Stack: —
- Code: 477 lines in 13 files (JavaScript 348, CSS 62, HTML 57, JSON 22, YAML 15, Docker 10, Markdown 7)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

## Security and compliance review

**88/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.28) of the process, the code, the hosting plan and the live app.

A zero-dependency Node.js dashboard running as a non-root container on a paid DigitalOcean App Platform instance, with no secrets involved, a strict static-file allowlist, validated inputs and escaped client rendering. HTTPS and the HTTP-to-HTTPS redirect work correctly. The weaknesses are minor: the base image isn't digest-pinned, the deployed image tag is mutable and was pushed from a workstation, and the app sends no security headers (HSTS, nosniff, frame protection, CSP).

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 10/10 | The app needs no credentials, none appear in source, image or logs, and registry access used doctl's own login flow without printing tokens. .env is excluded via .gitignore/.dockerignore. |
| Deployment provenance | 20 | 7/10 | The image was built locally from the reviewed source with zero npm dependencies and pushed to an owner-controlled DOCR registry, but the base image node:22-alpine is not digest-pinned, the deployed tag v1 is mutable, and doctl was installed from a GitHub tarball without checksum verification. |
| Terms compliance | 15 | 9/10 | Commercial use on a paid App Platform basic instance ($5/mo, always-on, not sleeping) plus a free starter registry tier, both of which allow commercial use under DigitalOcean's standard terms. The account plan wasn't readable, so this assumes a normal paid account. |
| Least privilege | 15 | 9/10 | Single App Platform service running as the non-root 'node' user, no database or extra public resources, and the CSV is baked read-only into the image. Minor: the registry login was left at the default 30-day credential lifetime on the build host. |
| Transport security | 10 | 8/10 | HTTPS works with a valid Google Trust Services certificate and HTTP returns a 301 redirect to HTTPS, but the app sets no HSTS, X-Content-Type-Options, frame protection or CSP headers even though it could easily add them. |
| Attack surface | 10 | 10/10 | Only the three static files and the API/health routes are served through an explicit allowlist. Probes for .env, .git/config, package.json, source, the CSV, the Dockerfile and path traversal all returned 404/400 with no stack traces. |
| Application security | 5 | 8/10 | Inputs are validated (dates by regex, filters by exact match, limit capped at 500), non-GET methods are rejected, errors are generic, and the client escapes all data before using innerHTML. Missing: CSP/security headers and any application-level rate limiting, and Date.parse accepts impossible dates such as 2025-02-31. |

Findings:

- **low** · deployment · Base image not pinned by digest: app/Dockerfile line 1: FROM node:22-alpine Fix: Pin the base image by digest (node:22-alpine@sha256:...) and update it on purpose.
- **low** · deployment · Mutable image tag deployed; built from an ad-hoc workstation, not CI: app/.do/app.yaml: image tag 'v1'; process/deploy.md: docker build ... && docker push registry.digitalocean.com/adb-6mbv0-dataviz/adb-6mbv0-dataviz-web:v1 (digest sha256:97c7c564...) Fix: Deploy by immutable digest or unique per-commit tags, ideally built by CI from a repository the owner controls.
- **low** · deployment · doctl downloaded without checksum verification: process/deploy.md: curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ (doctl was already installed, so this branch did not run) Fix: Verify the release checksum or install from a trusted package source.
- **low** · app · No security headers (HSTS, nosniff, frame protection, CSP): curl -sI https://adb-6mbv0-dataviz-dyatk.ondigitalocean.app/ returns only content-type, cache-control and platform headers; app/src/server.js send() sets only Content-Type and Cache-Control Fix: Add Strict-Transport-Security, X-Content-Type-Options: nosniff, X-Frame-Options/frame-ancestors and a restrictive Content-Security-Policy in send().
- **info** · deployment · Registry credential left at the 30-day default: process/deploy.md: doctl registry login -> 'Login valid for 30 days' Fix: Use --expiry-seconds for short-lived registry logins on build hosts.
- **info** · app · No application-level rate limiting on public API: app/src/server.js: /api/summary and /api/orders have no throttling; GET /api/orders?limit=99999 returned 500 rows (capped) Fix: Rely on platform/Cloudflare protections or add simple per-IP rate limiting; the cap on limit already bounds the cost of each response.
- **info** · app · Impossible calendar dates accepted: GET /api/summary?start=2025-02-31 returned 200 with filtered data; app/src/data.js parseFilters uses DATE_RE plus Date.parse, which rolls dates over Fix: Round-trip the date through toISOString().slice(0,10) and reject it if the result differs.

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
| Light use | $5.00 | fixed monthly prices; 0.0373 GiB out of a 50 GiB allowance |
| Busy | $5.00 | fixed monthly prices; 49 GiB out of a 50 GiB allowance |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| app | adb-6mbv0-dataviz | adb-6mbv0-dataviz-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-6mbv0-dataviz-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-6mbv0-dataviz | starter | $0.00 | Container Registry starter tier (one per account) |

Teardown: 2 deleted

## Agent's deploy summary

> The dashboard is live at **https://adb-6mbv0-dataviz-dyatk.ondigitalocean.app**, and every `TASK.md` requirement checked out through that URL. Nothing needed a person to step in.
>
> **What I deployed:**
> - **Container Registry** `adb-6mbv0-dataviz` on the free starter tier. The app's Docker image `adb-6mbv0-dataviz-web:v1` is stored there.
> - **App Platform app** `adb-6mbv0-dataviz`, running one service, `adb-6mbv0-dataviz-web`, on the smallest paid size (`apps-s-1vcpu-0.5gb`) in New York. The settings are in `.do/app.yaml`. HTTPS comes from App Platform's default `ondigitalocean.app` address, and `/healthz` is the health check.
> - **Estimated cost:** about $5/month, all for the app service; the registry is free.
>
> **Checked through the public URL:**
> - The dashboard page and its files load.
> - `/api/summary` returns the same results as locally: unfiltered totals, a combined region + category + date filter, and zeros with empty arrays when nothing matches.
> - `/api/orders` returns filtered, paginated rows.
> - A screenshot of the live page with the Software filter applied shows the KPIs, both charts and the table all updated.
>
> **Before you deploy a new version:** build and push a new image tag, change the tag in `.do/app.yaml`, then run `doctl apps update 77d60e13-3186-4272-aa75-443bd5b1ae15 --spec .do/app.yaml`.
>
> I didn't create any credentials, so there's no `.env`. I added `.env` to `.gitignore` and `.dockerignore` anyway. The resource details are in `deployment.json`.

## Shell commands during deploy

- `5s` `which doctl || (cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/); doctl version; doctl a`
- `9s` `cd /home/runner/work/_temp/adb-6mbv0-dataviz; doctl registry create adb-6mbv0-dataviz --subscription-tier starter --region nyc3 2>&1 && doctl registry login 2>&1 | tail -1 && docker build -q -t regist`
- `30s` `cd /home/runner/work/_temp/adb-6mbv0-dataviz; mkdir -p .do; cat > .do/app.yaml <<'EOF'`
- `54s` ❌ `doctl apps list --format ID,Spec.Name,DefaultIngress,Phase 2>&1`
- `56s` `doctl apps list -o json | python3 -c "import json,sys;[print(a['id'],a['spec']['name'],a.get('default_ingress'),a.get('active_deployment',{}).get('phase')) for a in json.load(sys.stdin)]"`
- `1m 01s` `U=https://adb-6mbv0-dataviz-dyatk.ondigitalocean.app; curl -s -o /dev/null -w "/ %{http_code}\n" $U/; curl -s $U/ | grep -o "<title>.*</title>"; curl -s "$U/api/summary" | head -c 150; echo; curl -s "`
- `1m 14s` `cd /home/runner/work/_temp/adb-6mbv0-dataviz; echo ".env" >> .gitignore; echo ".env" >> .dockerignore`
