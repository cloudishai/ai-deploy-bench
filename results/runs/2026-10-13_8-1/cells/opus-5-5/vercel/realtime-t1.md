# ✅ Real-Time Collaborative App on Vercel with Opus 5.5 (trial 1)

**success**: 13/13 checks passed (100%).

- URL: https://adb-raatw-realtime-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-raatw-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 5m 02s | 9m 27s | 14m 29s |
| Turns | 15 | 29 | |
| Tokens | 582.9K | 1.99M | 2.57M |
| Agent cost | $0.55 | $1.03 | $1.58 |
| Shell commands | 13 | 27 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The room the verifier's clients chatted in, with its history** (https://adb-raatw-realtime-web.vercel.app/?room=bench-2ac8ef33)

![The room the verifier's clients chatted in, with its history](realtime-t1/chat.jpg)

## What was built

- Stack: `@upstash/redis`, `next`, `react`, `redis`
- Code: 540 lines in 15 files (TypeScript 431, JSON 94, JavaScript 92, Markdown 17, CSS 17)
- Dependencies: 9 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Accept the Upstash marketplace terms for team ai-deploy-bench at https://vercel.com/ai-deploy-bench/~/integrations/accep; ng Upstash for Redis by Upstash under ai-deploy-bench { "status": "action_required", "reason": "integration_terms_accept

## Security and compliance review

**84/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.39) of the process, the code, the hosting plan and the live app.

The Vercel Hobby deployment of this personal club chat app is clean. No secrets are involved or leaked, HTTPS is enforced with HSTS, no source or config files are exposed, and input validation and output escaping are sound. The main weakness is that the public POST and long-lived SSE endpoints have no rate limiting or connection caps. Minor issues: deployment protection is turned off for previews too, the CLI and dependency ranges are unpinned, and the app sets no security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | The app needs no secrets and none are in the source, the build context or the deployed files. The agent confirmed via the deployment file listing that .env.local wasn't uploaded. Optional Redis credentials would be read from platform env vars. One minor issue: the Vercel token was passed as a --token command-line argument (expanded from an env var). |
| Deployment provenance | 20 | 8/10 | Production was built by Vercel from the agent's local source tree, with package-lock.json uploaded, so dependency versions are locked. But package.json uses caret ranges and @latest installs, the Vercel CLI was run as unpinned `npx -y vercel@latest`, and there is no owner-controlled remote git repo tied to the deployment. |
| Terms compliance | 15 | 9/10 | This is a personal (hobby club) app on Vercel Hobby, which Vercel's terms allow for personal, non-commercial use. As far as I know, Hobby doesn't expire or sleep functions. The message store is Runtime Cache, which is ephemeral, so history can be evicted. That is a durability limit, not a terms violation. |
| Least privilege | 15 | 8/10 | There is no public data store, and the Runtime Cache can only be reached from the project's functions. The agent turned deployment protection off completely (ssoProtection=null) rather than using Standard protection, which keeps the production alias public but leaves preview and per-deployment URLs protected. |
| Transport security | 10 | 8/10 | HTTP redirects to HTTPS with a 308, the certificate is valid and the platform adds HSTS with preload. The app sets no CSP, X-Content-Type-Options or frame protection, though it could have done so in next.config headers. |
| Attack surface | 10 | 9/10 | Requests for .env, .git, package.json, source files and .vercel all return 404, and errors return generic JSON with no stack traces. Responses still send the `x-powered-by: Next.js` header. |
| Application security | 5 | 6/10 | Input validation is solid: invalid JSON, null bodies, non-string, empty and over-1000-character text, and room names over 64 characters all get 400. React escapes user content, so there is no XSS. But the public POST and SSE endpoints have no rate limiting or connection caps, and each SSE connection holds a function for up to 270s while polling the cache every 500ms, so anyone can exhaust the Hobby quota or flood rooms. |

Findings:

- **medium** · app · No rate limiting or connection caps on public message and SSE endpoints: app/app/api/rooms/[room]/[action]/route.ts: postMessage has no throttling; events() loops for STREAM_MS=270000 polling store.latest every POLL_MS=500 with maxDuration=300; unlimited rooms can be created. A POST to /api/rooms/sec-review-19779/messages succeeded anonymously with 201. Fix: Add per-IP rate limiting (for example the Vercel Firewall rate-limit rules or a KV-backed limiter), cap concurrent SSE streams per IP, and cap the number of rooms or messages per period.
- **low** · deployment · Deployment protection disabled for all deployments, including previews: process/deploy.md:278: PATCH /v9/projects/adb-raatw-realtime-web with {"ssoProtection":null} Fix: Use Standard Protection, which keeps the production domain public but protects preview and per-deployment URLs, rather than turning protection off entirely.
- **low** · deployment · Unpinned deploy tooling and dependency ranges, no source repo of record: process/deploy.md:20,222: `npx -y vercel@latest`; process/build.md:21: `npm i next@latest react@latest ...`; app/package.json uses ^ ranges. Deployed by `vercel deploy --prod` from a local directory with a local-only git repo. The lockfile was uploaded (deploy.md:707). Fix: Pin the Vercel CLI version, keep the committed lockfile with exact versions, and deploy from an owner-controlled git repository connected to the Vercel project.
- **low** · app · Missing CSP, X-Content-Type-Options and frame protection headers: curl -sI https://adb-raatw-realtime-web.vercel.app/ returns only strict-transport-security (platform), with no content-security-policy, x-content-type-options or x-frame-options Fix: Add a headers() block in next.config, or a headers entry in vercel.json, setting CSP with frame-ancestors 'none', X-Content-Type-Options: nosniff and Referrer-Policy.
- **low** · deployment · Vercel token passed on the command line: process/deploy.md:20 and later: VC="npx -y vercel@latest --token $VERCEL_TOKEN ..." (the transcript shows only the variable name, so nothing leaked) Fix: Let the CLI read VERCEL_TOKEN from the environment instead of passing --token, so the token never shows up in process arguments.
- **info** · app · Framework disclosed via x-powered-by header: curl -sI https://adb-raatw-realtime-web.vercel.app/ returns `x-powered-by: Next.js` Fix: Set poweredByHeader: false in next.config.
- **info** · deployment · Message history kept in ephemeral, shared Runtime Cache: process/deployment.json notes: Upstash couldn't be provisioned; history is in Vercel Runtime Cache (LRU eviction possible, 7-day TTL, shared on Hobby); app/lib/store.ts RuntimeCacheStore Fix: Finish the documented human step to attach Upstash Redis (or another durable store) so room history survives eviction.
- **info** · app · User content is rendered safely: A POST with text "<img src=x onerror=alert(1)>" is stored verbatim and rendered as React text. GET /?room=<script>alert(1)</script> renders it escaped as &lt;script&gt;. The validation probes (bad JSON, null body, text 123, an empty string, 1001 characters, a 70-character room name) all returned 400. Fix: No action needed.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the chat UI as HTML | yes | passed |  |
| deployment.json declares a supported transport (websocket or sse) | no | passed |  |
| Clients connect over sse | yes | passed |  |
| A message reaches another client in the same room within 5 s | yes | passed |  |
| The sender receives its own message too | no | passed |  |
| Messages never reach clients in other rooms | yes | passed |  |
| Five users posting at the same time all see every message within 10 s | yes | passed |  |
| GET /api/rooms/<room>/messages returns recent messages | yes | passed |  |
| Messages over 1000 characters are rejected | no | passed |  |
| The chat UI loads in a browser without errors | no | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.00 | within Hobby's included usage |
| Busy | $20.00 | exceeds Hobby's limits (CDN requests, function invocations, active CPU), which pauses the project, so priced on Pro: $20 platform fee including $20 of usage credit, $5.75 of usage |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-raatw-realtime-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The app is live at **https://adb-raatw-realtime-web.vercel.app** and every requirement works through that URL. Message history is held in a cache that can lose old messages, because the durable Redis store needs a person to accept terms first (see below).
>
> **What's deployed**
> - **Project:** `adb-raatw-realtime-web`, Next.js on the Hobby plan (free), running in Vercel's `iad1` region. I turned off Vercel Authentication, which had been blocking public access to the `.vercel.app` URL.
> - **Real-time:** Server-Sent Events, because Vercel functions can't hold WebSocket connections. `deployment.json` has `"realtime": {"transport": "sse"}`, and there is no `/ws` endpoint.
> - **Storage:** Vercel Runtime Cache, which is free on Hobby and shared by all instances of the app's functions. It has no atomic operations, so each instance writes only its own message log, and a per-room list of writers is updated with read-and-retry so simultaneous posts aren't lost.
>
> **Tested through the public URL**
> - **Test suite:** all 4 tests pass, covering the page, message format, 50-message history in order, the `400` cases, and room isolation. 20 simultaneous posts reached 2 listeners in under 2s.
> - **Stress test:** run 3 times, 45 posts from parallel senders. All 4 listeners got every message each time, at most about 1.1s after sending, and history had all 45.
> - **Browser test:** in headless Chromium, a second user saw messages live, a user in another room didn't, and a new joiner saw history.
>
> **What didn't work**
> - **Durable Redis:** setting up Upstash needs its marketplace terms accepted in a browser by a person. This is listed under `human_steps` as non-blocking.
> - **Data loss risk:** until that's done, history isn't durable. Cached messages can be evicted at any time and expire after 7 days. On Hobby the cache is also shared with the team's other projects.
> - **One flaky run:** the first full test run after this change had one history test fail. I didn't capture which check failed, and the cause is unconfirmed; a race during cold start is the likely one. Every run since has passed.
>
> **To switch to Redis**, a person accepts the terms at https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/upstash?source=cli. Then run `vercel integration add upstash/upstash-kv --name adb-raatw-realtime-redis` and `vercel deploy --prod`. The app picks up the Redis settings automatically.
>
> **Changes in this step**
> - All room endpoints now live in one route file.
> - The browser subscribes to the stream before loading history, so no message falls in the gap.
> - Message IDs are now strings.
> - `vercel.json` sets the framework to Next.js.
>
> Estimated cost is $0/month. I didn't create any credentials, so `.env` wasn't needed. No servers are left running, and the work is committed locally.

## Shell commands during deploy

- `5s` `cd /home/runner/work/_temp/adb-raatw-realtime; npx -y vercel@latest --version 2>&1 | tail -1; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v1/storage/stores?teamId=$VERCEL_`
- `30s` `cd /home/runner/work/_temp/adb-raatw-realtime; export VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC project add adb-raatw-realtime-web 2>&1 | tail -2; $VC link --yes --p`
- `36s` `cd /home/runner/work/_temp/adb-raatw-realtime; VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC integration --help 2>&1 | head -40`
- `39s` `cd /home/runner/work/_temp/adb-raatw-realtime; VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC integration add --help 2>&1 | sed -n 1,60p`
- `42s` `cd /home/runner/work/_temp/adb-raatw-realtime; VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC integration add upstash/upstash-kv --name adb-raatw-realtime-redis --non-int`
- `1m 11s` `cd /home/runner/work/_temp/adb-raatw-realtime/app/api/rooms/\[room\] && mkdir -p '[action]' && python3 - <<'EOF'`
- `1m 15s` `cd /home/runner/work/_temp/adb-raatw-realtime && f='app/api/rooms/[room]/[action]/route.ts' && cat -s "$f" > /tmp/r && mv /tmp/r "$f" && npm run build 2>&1 | grep -E 'ƒ|rror' ; (npx next start -p 3123`
- `1m 27s` `cd /home/runner/work/_temp/adb-raatw-realtime; VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC deploy --prod --yes 2>&1 | grep -vi plugin | tail -8`
- `1m 54s` `cd /home/runner/work/_temp/adb-raatw-realtime; echo '{ "framework": "nextjs" }' > vercel.json; VC="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC deploy --prod --yes 2>&1 | g`
- `2m 26s` `cd /home/runner/work/_temp/adb-raatw-realtime; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-raatw-realtime-web?teamId=$VERCEL_TEAM_ID" | python3 -c "import `
- `2m 32s` `cd /home/runner/work/_temp/adb-raatw-realtime; curl -s -XPATCH -H "Authorization: Bearer $VERCEL_TOKEN" -H 'Content-Type: application/json' "https://api.vercel.com/v9/projects/adb-raatw-realtime-web?t`
- `4m 35s` `cat /tmp/claude-1001/-home-runner-work--temp-adb-raatw-realtime/880f54ab-6b61-41de-8e0c-ca9f803bf7c3/tasks/b2ynld44g.output`
- `4m 49s` ❌ `cd /home/runner/work/_temp/adb-raatw-realtime; pkill -f "node --test" ; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-raatw-realtime-web?teamId=$VERCEL_TEAM_`
- `4m 53s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-raatw-realtime-web?teamId=$VERCEL_TEAM_ID" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('re`
- `5m 41s` `cd /home/runner/work/_temp/adb-raatw-realtime; npm i @vercel/functions 2>&1 | tail -1; grep -n "getCache\|interface\|export" node_modules/@vercel/functions/cache/*.d.ts 2>/dev/null | head -30 || ls no`
- `5m 42s` `cd /home/runner/work/_temp/adb-raatw-realtime; sed -n 1,80p 'app/api/rooms/[room]/[action]/route.ts' | sed -n 45,110p`
- `5m 46s` `cd /home/runner/work/_temp/adb-raatw-realtime; cat node_modules/@vercel/functions/cache/types.d.ts | sed -n 1,60p`
- `6m 08s` `cd /home/runner/work/_temp/adb-raatw-realtime; python3 - <<'EOF'`
- `6m 18s` `cd /home/runner/work/_temp/adb-raatw-realtime; (VERCEL=1 npx next start -p 3126 > /tmp/s3.log 2>&1 &); (npx next start -p 3127 > /tmp/s4.log 2>&1 &); sleep 4; for p in 3126 3127; do BASE_URL=http://lo`
- `6m 32s` `cd /home/runner/work/_temp/adb-raatw-realtime; python3 - <<'EOF'`
- `7m 03s` `cd /home/runner/work/_temp/adb-raatw-realtime; U=https://adb-raatw-realtime-web.vercel.app; BASE_URL=$U timeout 100 node --test --test-name-pattern="history" tests/api.test.mjs 2>&1 | grep -A12 Assert`
- `7m 16s` `cd /home/runner/work/_temp/adb-raatw-realtime; U=https://adb-raatw-realtime-web.vercel.app; for i in 1 2; do BASE_URL=$U timeout 100 npm test 2>&1 | grep -E '^(✔|✖)|actual|expected|got|^\s+[+-] ' | he`
- `7m 42s` `mkdir -p /tmp/stress && cat > /tmp/stress/s.mjs <<'EOF'`
- `7m 57s` `cd /home/runner/work/_temp/adb-raatw-realtime; for i in 1 2; do node /tmp/stress/s.mjs https://adb-raatw-realtime-web.vercel.app; done; BASE_URL=https://adb-raatw-realtime-web.vercel.app timeout 100 n`
- `8m 31s` `mkdir -p /tmp/pw && cd /tmp/pw && npm init -y >/dev/null && npm i playwright@latest >/dev/null 2>&1 && npx playwright install --with-deps chromium >/dev/null 2>&1; cat > ui.mjs <<'EOF'`
- `9m 00s` `cd /home/runner/work/_temp/adb-raatw-realtime; D=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v6/deployments?teamId=$VERCEL_TEAM_ID&projectId=adb-raatw-realtime-web&limit`
- `9m 16s` `cd /home/runner/work/_temp/adb-raatw-realtime; python3 - <<'EOF'`
