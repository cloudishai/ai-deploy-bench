# ⚠️ API / Backend Service on Vercel with Opus 5.5 (trial 1)

**partial** (failed at human): 11/20 checks passed (55%).

- URL: https://adb-isyxt-api.vercel.app (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-isyxt-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 32s | 6m 56s | 9m 28s |
| Turns | 10 | 25 | |
| Tokens | 421.0K | 1.60M | 2.02M |
| Agent cost | $0.52 | $0.82 | $1.34 |
| Shell commands | 9 | 24 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-isyxt-api.vercel.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `@vercel/blob`, `express`, `pg`
- Code: 693 lines in 15 files (JavaScript 693, JSON 46, Markdown 20)
- Dependencies: 4 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

3 step(s), about 8 min of a person's time. **Blocked:** the deploy couldn't finish without them.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup
- **Install a Marketplace integration and accept its terms in a browser** (~3 min): tool output: 21.0) > Installing Neon by Neon under ai-deploy-bench { "status": "action_required", "reason": "integration_terms_acceptance_required", "message": "Accept marketplace terms for \"Neon\" in your browser before this install can finis

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.47) of the process, the code, the hosting plan and the live app.

The agent deployed a well-built Notes API on Vercel Hobby, which fits this personal project. Secrets are handled properly through Vercel env vars, storage is a private Blob store, HTTPS is enforced, and authentication, ownership and validation are correct. The main weakness is that the catch-all rewrite with framework:null leaves the project's source files (src/*.js, dev-server.js, TASK.md) publicly downloadable. They contain no secrets. Smaller issues: unpinned deploy tooling, deploys made from a local directory, missing app-set security headers, and no field length limits.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS was piped through stdin into Vercel's encrypted env vars, the Blob token was put in place by the store connection, and nothing secret is in source, logs or deployed files (.env is excluded by .vercelignore). One small issue: the Vercel token was passed as a --token command-line argument. |
| Deployment provenance | 20 | 7/10 | Production runs the agent's code, deployed straight from its own working directory with the Vercel CLI, and a package-lock.json was uploaded. The CLI was installed as vercel@latest without a pin, package.json uses caret ranges, and the deploy has no git/CI link to an owner-controlled repo. |
| Terms compliance | 15 | 9/10 | This is a personal side project on Vercel Hobby, and Hobby's terms allow non-commercial personal use. The Hobby Blob free-tier operation caps could pause the store under heavy use, and the agent documented that. |
| Least privilege | 15 | 8/10 | The Blob store is private, there are no containers or public data stores, and only the needed env vars exist. The store-wide read-write Blob token was also given to the development environment, which doesn't need it. |
| Transport security | 10 | 9/10 | HTTP returns a 308 redirect to HTTPS, the certificate is valid, and the platform sets HSTS with preload. The app doesn't set X-Content-Type-Options, frame protection or a CSP, though it could have (it is a JSON API with one static docs page). |
| Attack surface | 10 | 5/10 | Because of the catch-all rewrite with framework:null, the project's root files are served as static assets, so the app's source (/src/create-app.js, /src/store/*.js, /dev-server.js) and TASK.md are publicly downloadable. They contain no secrets. Unknown paths, .env, .git and package.json return 404 JSON, and errors don't leak stack traces. |
| Application security | 5 | 8/10 | Input validation is solid, key comparison is constant-time, ownership is scoped by a key hash with 404s for other owners, the Postgres path uses parameterized SQL, and rate limiting is per key. Minor gaps: no length limits on title, content or tags beyond the 1 MB body cap, a fixed window that allows a burst of up to ~120 requests at a minute boundary, and JSON parsing that runs before authentication. |

Findings:

- **medium** · deployment · Application source code served publicly as static files: GET https://adb-isyxt-api.vercel.app/src/create-app.js -> 200 application/javascript (full source); /src/store/blob.js, /src/store/index.js, /src/openapi.js, /dev-server.js and /TASK.md also return 200. vercel.json uses framework:null with a rewrite /(.*) -> /api, and .vercelignore only excludes .env*, node_modules, test and deployment.json. Fix: Add TASK.md and dev-server.js to .vercelignore. For src/, which the function still needs, either move the code under api/ (for example api/_lib), set an empty public outputDirectory so no project files are served statically, or bundle the function so its source isn't uploaded as static assets.
- **low** · deployment · Unpinned deploy tooling and no source-controlled deploy: process/deploy.md: `npm i -g vercel@latest`, then `vercel deploy --prod` from the local working directory (`git` reports 'not a git repository'). package.json uses caret ranges (^2.8.1, ^5.3.0, ^8.23.1). Fix: Pin the Vercel CLI version and deploy from a git repository the owner controls (Vercel Git integration or CI), with the lockfile committed.
- **low** · deployment · Vercel token passed on the command line: process/deploy.md: commands such as `vercel deploy --prod --yes --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID` put the token in process arguments. Fix: Export VERCEL_TOKEN in the environment (the CLI reads it) instead of passing --token.
- **low** · deployment · Blob read-write token granted to development environment: process/deploy.md: store connection with envVarEnvironments ["production","preview","development"]; env list shows `BLOB_READ_WRITE_TOKEN production,preview,development`, and `vercel env pull` wrote it into a local .env. Fix: Connect the production store only to production (and a separate store for preview/dev if needed).
- **low** · app · Missing security headers the app could set: curl -I https://adb-isyxt-api.vercel.app/docs: only strict-transport-security (added by the platform). No X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy. src/create-app.js sets no headers. Fix: Set nosniff, frame-ancestors 'none' and a restrictive CSP, either in Express middleware or in vercel.json headers.
- **low** · app · No field length limits; fixed-window rate limit allows boundary bursts: src/create-app.js: validateTitle/validateContent/validateTags check only type and emptiness, and express.json limit is 1mb. Rate limiting uses Math.floor(now / WINDOW_MS) fixed windows, so up to ~120 requests can land around a minute boundary. Fix: Cap title, content and tag lengths and the number of tags, and consider a sliding-window limiter.
- **info** · app · Request body parsed before authentication: POST /v1/notes with no X-API-Key and body '{bad' -> 400 {"error":"Malformed JSON body"} instead of 401 (express.json is mounted app-wide before the v1 auth middleware). Fix: Mount express.json after authenticate on the /v1 router so unauthenticated requests are rejected before parsing.
- **info** · platform · Hobby Blob free-tier operation caps: process/deployment.json notes: about 2-3 advanced Blob operations per API request against the Hobby monthly cap. Hobby suspends usage past the included limits until the next cycle. Fix: Fine for a personal project. Switch to Postgres (Neon) as documented if usage grows.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET /health answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET /health returns {status: ok} | yes | passed |  |
| GET /openapi.json is an OpenAPI 3 document covering /v1/notes | yes | passed |  |
| GET /docs serves human-readable documentation | no | passed |  |
| Requests without an API key get 401 | yes | passed |  |
| Requests with an unknown API key get 401 | yes | passed |  |
| POST /v1/notes creates a note | yes | failed | POST /v1/notes returned 429, expected 201 or 200: {"error":"Rate limit exceeded: 60 requests per minute. Retry in 10s."} |
| Invalid notes are rejected with 400 | yes | failed | missing title: expected 400, got 429 |
| GET /v1/notes/{id} returns the note | yes | failed | not run: depends on create |
| GET /v1/notes lists notes and filters by tag | yes | failed | not run: depends on create |
| Notes are listed newest first | no | failed | not run: depends on create |
| PATCH /v1/notes/{id} updates only the given fields | yes | failed | not run: depends on create |
| Notes are private to the API key that created them | yes | failed | not run: depends on create |
| DELETE /v1/notes/{id} removes the note | yes | failed | not run: depends on create |
| Notes are still there a minute later | yes | failed | not run: depends on create |
| Exceeding 60 requests/minute returns 429 | yes | passed |  |
| 429 responses include a Retry-After header | no | passed |  |
| One key hitting its limit doesn't throttle other keys | yes | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.00 | within Hobby's included usage |
| Busy | $20.00 | exceeds Hobby's limits (CDN requests, function invocations, active CPU), which pauses the project, so priced on Pro: $20 platform fee including $20 of usage credit, $5.75 of usage |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-isyxt-api | — | $0.00 | no fixed fee; usage within the plan's included allowance |
| blob_store | adb-isyxt-api-blob | — | $0.00 | usage-billed; free within plan allowance |

Teardown: 2 deleted

## Agent's deploy summary

> The API is live at **https://adb-isyxt-api.vercel.app**. Every requirement in `TASK.md` works through that URL, but it stores data in Vercel Blob, not the Postgres database I planned.
>
> **What's deployed**
> - **Project `adb-isyxt-api`** on the free Hobby plan. It runs the Express app as one serverless function.
> - **Private Vercel Blob store `adb-isyxt-api-blob`** (free tier). It holds the notes and the per-key request counts for rate limiting.
> - **`API_KEYS`** is set to exactly the two keys in `BENCH_API_KEYS`, for production and preview.
> - **Cost:** $0 a month.
>
> **Why Blob instead of Postgres:** adding Neon, Vercel's Postgres option, needs a person to accept its terms in a browser. I didn't want to leave the app without a database. So I added a second storage option on Vercel Blob, which needed no terms. The app picks its storage when it starts: Postgres if a database connection string is set, otherwise Blob. The tests pass with both.
>
> **Tested through the public URL with the benchmark keys:**
> - `/health`, `/openapi.json` and `/docs` work without a key.
> - Missing or wrong keys get `401`.
> - Bad input (empty title, wrong types) gets `400`.
> - Create, read, update, delete and list work. Lists come back newest first, and the tag filter works.
> - One key can't read, list, change or delete another key's notes; it gets `404`.
> - A note was still there after a redeploy.
> - **Rate limit:** 61 requests in a row gave 60 successes, then a `429` with a `Retry-After` header. A burst of 70 at once also gave exactly 60 successes. The other key wasn't affected.
>
> **Limitations of running on Blob**
> - Each request takes about 100–300 ms longer than it would with Postgres.
> - The free Blob tier caps write and list operations per month, and each API request uses 2–3 of them. Very heavy use could hit that cap until the next month.
> - The rate limit resets at each calendar minute rather than using a sliding 60-second window.
>
> **Optional human step** (recorded in `deployment.json`, not blocking): accept the Neon terms at https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon. Then run `vercel integration add neon --name adb-isyxt-api-db` and redeploy. The app switches to Postgres automatically, which removes the latency and the monthly cap. Notes already stored in Blob would not be moved across.
>
> The Blob access token is saved in `.env`, which is excluded from both git and the deployment. I stopped the local Postgres container.

## Shell commands during deploy

- `4s` `npm i -g vercel@latest >/dev/null 2>&1; vercel --version; echo "BENCH keys count: $(echo $BENCH_API_KEYS | tr ',' '\n' | wc -l)"; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.c`
- `23s` `vercel integration --help 2>&1 | head -40; vercel integration add --help 2>&1 | head -40`
- `28s` `export VERCEL_ORG_ID=$VERCEL_TEAM_ID; vercel project add adb-isyxt-api --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID 2>&1 | tail -3; vercel link --yes --project adb-isyxt-api --token $VERCEL_TOKEN --s`
- `32s` `cat .vercel/project.json; echo; vercel integration add neon --help --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID 2>&1 | sed -n '1,60p' | grep -vi telemetry`
- `41s` `timeout 180 vercel integration add neon --name adb-isyxt-api-db --non-interactive --no-env-pull --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID < /dev/null 2>&1 | grep -vi telemetry | grep -v '^\s*$' | `
- `55s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v2/teams/$VERCEL_TEAM_ID" | node -pe 'const t=JSON.parse(require("fs").readFileSync(0)); JSON.stringify({plan:t.billing&&t.bill`
- `1m 08s` ❌ `npm i @vercel/blob 2>&1 | tail -1 && node -p 'require("@vercel/blob/package.json").version' && grep -oE "declare function [a-zA-Z]+|access\?*: [^;]+" node_modules/@vercel/blob/dist/index.d.ts | sort -`
- `1m 14s` `cd /home/runner/work/_temp/adb-isyxt-api/node_modules/@vercel/blob && grep '"version"' package.json; ls dist | head; grep -nE "^declare (function|const) |access" dist/index.d.ts | head -60`
- `1m 18s` `sed -n 180,235p dist/index.d.ts; grep -nE "interface ListBlobResultBlob|interface ListCommandOptions" -A 14 dist/index.d.ts | head -50`
- `1m 23s` `cd /home/runner/work/_temp/adb-isyxt-api && curl -s -X POST -H "Authorization: Bearer $VERCEL_TOKEN" -H 'content-type: application/json' "https://api.vercel.com/v1/storage/stores/blob?teamId=$VERCEL_T`
- `1m 28s` `curl -s -X POST -H "Authorization: Bearer $VERCEL_TOKEN" -H 'content-type: application/json' "https://api.vercel.com/v1/storage/stores/store_GVuV5GjvpRD8M8CY/connections?teamId=$VERCEL_TEAM_ID" -d '{"`
- `1m 34s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v9/projects/adb-isyxt-api/env?teamId=$VERCEL_TEAM_ID" | node -pe 'JSON.parse(require("fs").readFileSync(0)).envs.map(e=>e.key+"`
- `1m 47s` `vercel env pull .env --environment development --yes --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID >/dev/null 2>&1; sed -E 's/=.*/=<set>/' .env; sed -n 1,40p src/db.js | head -5`
- `2m 11s` `mkdir -p src/store && git mv 2>/dev/null; mv src/db.js src/store/pg-client.js && cat > src/store/postgres.js <<'EOF'`
- `2m 22s` `python3 - <<'EOF'`
- `2m 31s` `python3 - <<'EOF'`
- `2m 56s` `printf '.env\n.env*\nnode_modules\ntest\ndeployment.json\n' > .vercelignore && vercel deploy --prod --yes --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID 2>&1 | grep -vE "telemetry|^\s*$" | tail -8`
- `3m 12s` `vercel ls --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID 2>&1 | grep -vE "telemetry|^\s*$" | tail -5; vercel project inspect adb-isyxt-api --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID 2>&1 | grep -iE `
- `3m 17s` `U=https://adb-isyxt-api.vercel.app; curl -s -w " %{http_code}\n" $U/health; curl -s -o /dev/null -w "%{http_code} docs\n" $U/docs; curl -s $U/openapi.json | head -c 80; echo; curl -s -w " %{http_code}`
- `3m 26s` `U=https://adb-isyxt-api.vercel.app; K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1); K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2)`
- `3m 38s` `U=https://adb-isyxt-api.vercel.app; K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1); K2=$(echo "$BENCH_API_KEYS" | cut -d, -f2)`
- `3m 53s` `python3 - <<'EOF'`
- `5m 20s` `U=https://adb-isyxt-api.vercel.app; K1=$(echo "$BENCH_API_KEYS" | cut -d, -f1)`
- `6m 46s` `cat > deployment.json <<'EOF'`
