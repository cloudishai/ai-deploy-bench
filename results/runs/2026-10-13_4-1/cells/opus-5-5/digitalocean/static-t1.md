# ✅ Static Content Site on DigitalOcean with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-iwyf5-static-k39h3.ondigitalocean.app (from deployment.json)
- Estimated hosting: $5.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium
- Resource prefix: `adb-iwyf5-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 31s | 2m 26s | 3m 57s |
| Turns | 9 | 9 | |
| Tokens | 211.2K | 273.5K | 484.7K |
| Agent cost | $0.29 | $0.16 | $0.45 |
| Shell commands | 8 | 8 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 386 lines in 15 files (JavaScript 177, HTML 168, CSS 32, JSON 25, YAML 16, Docker 9, Markdown 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`, `.do/app.yaml`

## Human steps

3 step(s), about 7 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): prerequisite: account setup
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
| app | adb-iwyf5-static | adb-iwyf5-static-web: apps-s-1vcpu-0.5gb x 1 | $5.00 | adb-iwyf5-static-web: apps-s-1vcpu-0.5gb x 1 |
| registry | adb-iwyf5-static | starter | $0.00 | Container Registry starter tier (one per account) |
| project | adb-iwyf5-static | — | $0.00 | no charge at benchmark usage |

Teardown: 2 deleted, failed: adb-iwyf5-static, left over: adb-iwyf5-static

## Agent's deploy summary

> The site is live at **https://adb-iwyf5-static-k39h3.ondigitalocean.app**, and every requirement in `TASK.md` passes through that public URL.
>
> **How it's deployed:**
> - I built a Docker image from the existing `Dockerfile` and pushed it to a free DigitalOcean Container Registry named `adb-iwyf5-static` (as `adb-iwyf5-static-web:v1`).
> - It runs on App Platform as the app `adb-iwyf5-static`, with one web service on the smallest Basic size (`apps-s-1vcpu-0.5gb`) in the New York region. The app spec is saved in `.do/app.yaml`.
> - HTTPS comes with App Platform's default `ondigitalocean.app` address.
> - I put both in a DigitalOcean project named `adb-iwyf5-static`.
> - **Cost:** about $5/month, all for the web service; the registry is free.
>
> **What I checked on the public URL:**
> - `/`, `/about` and `/contact` return 200 with `text/html`, and each has a title, a viewport tag and navigation to the other pages.
> - Unknown paths and `.html` versions of the pages return 404.
> - `POST /api/contact` returns 200 with `{"ok":true}` for valid input. A missing name, an invalid email or an empty message each return 400 with an error message.
> - I filled in and submitted the contact form in a headless Chromium browser. It showed the confirmation message without reloading the page.
>
> **Choices I made:**
> - **Container image instead of Git:** App Platform usually builds from a Git repository, but there's no repository connected to this account, so I deployed the image instead.
> - **Web service instead of a static site:** the free static-site option can't run the contact endpoint, so I used a paid web service.
>
> Nothing needed a person, so `human_steps` in `deployment.json` is empty. Updating the site means building and pushing a new image tag, changing the tag in `.do/app.yaml`, and running `doctl apps update c0d1dff1-7855-4d7d-a6e4-faf4b865e6fe --spec .do/app.yaml`.

## Shell commands during deploy

- `6s` `which doctl; cd /tmp && curl -sL https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-linux-amd64.tar.gz | tar xz && sudo mv doctl /usr/local/bin/ ; doctl version; doctl acco`
- `11s` `doctl registry create adb-iwyf5-static --subscription-tier starter --region nyc3 && doctl registry login >/dev/null && docker build -q -t registry.digitalocean.com/adb-iwyf5-static/adb-iwyf5-static-we`
- `41s` `mkdir -p .do && cat > .do/app.yaml <<'EOF'`
- `1m 16s` `doctl apps list --format ID,Spec.Name,DefaultIngress,Phase; doctl projects list --format ID,Name,IsDefault`
- `1m 19s` `doctl apps list -o json | python3 -c "import json,sys;[print(a['id'],a['spec']['name'],a.get('default_ingress'),a.get('active_deployment',{}).get('phase'), a.get('in_progress_deployment',{}).get('phas`
- `1m 23s` `U=https://adb-iwyf5-static-k39h3.ondigitalocean.app`
- `1m 30s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i -s playwright >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1 && cat > t.js <<'EOF'`
- `2m 18s` `PID=$(doctl projects create --name adb-iwyf5-static --purpose "Web Application" --environment Production --format ID --no-header) && doctl projects resources assign $PID --resource=do:app:c0d1dff1-785`
