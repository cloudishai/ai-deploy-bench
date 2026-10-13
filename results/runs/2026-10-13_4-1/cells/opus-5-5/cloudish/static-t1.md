# ✅ Static Content Site on Cloudish with Opus 5.5 (trial 1)

**success**: 16/16 checks passed (100%).

- URL: https://adb-xtzco-static-web.on.do.cloudish.ai (from deployment.json)
- Estimated hosting: $7.84/month (the agent estimated $7.84)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium
- Resource prefix: `adb-xtzco-static`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 06s | 6m 53s | 8m 59s |
| Turns | 11 | 16 | |
| Tokens | 277.1K | 747.6K | 1.02M |
| Agent cost | $0.35 | $0.38 | $0.73 |
| Shell commands | 10 | 13 | |

App answered 0s after the agent finished deploying.

## What was built

- Stack: —
- Code: 452 lines in 13 files (JavaScript 211, HTML 177, CSS 56, JSON 40, Docker 8)
- Dependencies: 0 npm, 0 Python
- Deploy config: `Dockerfile`, `.dockerignore`

## Human steps

None: the agent needed no human setup at all.

Reported but not needed, since the deployment worked without them: Claim the Cloudish key 'adb-xtzco-static' and add credits: mint a fresh claim link with `GET https://cloudish.ai/api/v1/

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
| project | adb-xtzco-static-web | shared | $7.84 | 0.1 CPU / 0.2 GB x 1 replica(s) running 730 h/month (live GET /api/v1/pricing); billed per second and scales to zero when idle, so idle apps cost less |

Teardown: 1 deleted

## Agent's deploy summary

> The site is live on Cloudish at **https://adb-xtzco-static-web.on.do.cloudish.ai**, and every requirement in `TASK.md` passed when I tested it through that URL.
>
> **What I set up:**
> - **Cloudish key `adb-xtzco-static`:** created without signing up. It's saved in `.env`, which is gitignored and left out of what was uploaded.
> - **Project `adb-xtzco-static-web`:** Cloudish built the existing Dockerfile on its own servers. It runs on the cheapest size (`shared`: 0.1 CPU, 0.2 GB, one copy) and shuts down when idle. I swapped the random web address Cloudish assigned for a readable one.
>
> **Tested through the public URL:**
> - `/`, `/about` and `/contact` return 200 HTML pages with the required title, viewport tag, nav and content.
> - Unknown paths, including `/about.html`, return 404.
> - `POST /api/contact` returns 200 `{"ok":true}` for valid input, and 400 with an error message for a missing name, an invalid email or an empty message.
> - In a headless browser, the form showed an error and then a confirmation without reloading the page.
>
> **Cost:** about $0.011 per hour while the app is running, so at most $7.84 a month if it never shut down.
>
> **What a person needs to do:** the key only has Cloudish's free starting credit (about $0.095 left), which covers roughly 9 hours of running time. Once it runs out, the site returns errors (402 or 503) until credits are added. Someone needs to claim the key and add credits using a claim link. A link expires 30 minutes after it's created, so make a new one when needed. This is listed in `human_steps` in `deployment.json` and doesn't stop the site working now.
>
> The first request after the app has been idle takes a few seconds while it starts up again. Right after setup, the first couple of requests got no response before the app came up.

## Shell commands during deploy

- `4s` `curl -sL https://cloudish.ai/skill.md; echo ----; curl -sL https://cloudish.ai/instances.md`
- `11s` `grep -q CLOUDISH_API_KEY .env 2>/dev/null || {`
- `17s` `set -a && . ./.env && set +a && tar --exclude='.env*' --exclude='.git' --exclude='context.tar.gz' -czf /tmp/context.tar.gz Dockerfile .dockerignore package.json server.js public && tar tzf /tmp/contex`
- `23s` `. ./.env && for i in $(seq 1 40); do s=$(curl -s https://cloudish.ai/api/v1/images/builds/219 -H "Authorization: Bearer $CLOUDISH_API_KEY" | tee /tmp/b.json | python3 -c 'import json,sys;print(json.lo`
- `2m 26s` `cat /tmp/claude-1001/-home-runner-work--temp-adb-xtzco-static/80729b32-5dd0-4b62-b66b-de4158054ccb/tasks/bxewyn0ei.output | tail -5; python3 -c 'import json;d=json.load(open("/tmp/b.json"));print((d["`
- `2m 34s` `. ./.env && until s=$(curl -s https://cloudish.ai/api/v1/images/builds/219 -H "Authorization: Bearer $CLOUDISH_API_KEY" | tee /tmp/b.json | python3 -c 'import json,sys;print(json.load(sys.stdin)["buil`
- `2m 37s` `sleep 0; cat /tmp/claude-1001/-home-runner-work--temp-adb-xtzco-static/80729b32-5dd0-4b62-b66b-de4158054ccb/tasks/b4fykohx4.output; python3 -c 'import json;d=json.load(open("/tmp/b.json"));print(d["bu`
- `2m 43s` `f=/tmp/claude-1001/-home-runner-work--temp-adb-xtzco-static/80729b32-5dd0-4b62-b66b-de4158054ccb/tasks/b4fykohx4.output; for i in $(seq 1 55); do grep -qE '^(succeeded|failed)' $f && break; sleep 10; `
- `5m 47s` `. ./.env && curl -s https://cloudish.ai/api/v1/projects/adb-xtzco-static/adb-xtzco-static-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(js`
- `5m 52s` `. ./.env && curl -s https://cloudish.ai/api/v1/projects/adb-xtzco-static/adb-xtzco-static-web -H "Authorization: Bearer $CLOUDISH_API_KEY" | head -c 3000; echo; python3 -c 'import json;d=json.load(ope`
- `5m 56s` `. ./.env && curl -s -X PUT https://cloudish.ai/api/v1/projects/adb-xtzco-static/adb-xtzco-static-web/subdomain -H "Authorization: Bearer $CLOUDISH_API_KEY" -H "content-type: application/json" -d '{"la`
- `6m 03s` `U=https://adb-xtzco-static-web.on.do.cloudish.ai`
- `6m 34s` `. ./.env && curl -s https://cloudish.ai/api/v1/me -H "Authorization: Bearer $CLOUDISH_API_KEY" | python3 -c 'import json,sys;d=json.load(sys.stdin);a=d.get("apiKey",d);print({k:a.get(k) for k in ("ali`
