# ✅ API / Backend Service on Vercel with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-cy3y5-api.vercel.app (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-cy3y5-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 23s | 17m 45s | 21m 27s |
| Turns | 10 | 60 | |
| Tokens | 369.7K | 6.65M | 7.42M |
| Agent cost | $0.49 | $2.59 | $3.33 |
| Shell commands | 9 | 53 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 19s, 395.2K tokens, $0.25).

## Screenshots

**The API documentation at /docs** (https://adb-cy3y5-api.vercel.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Runtime: Node.js 20+
- Frameworks: Hono
- Libraries: Vercel Blob SDK, node-postgres, Vercel Functions helpers, @hono/node-server
- Dev tools: tsx, TypeScript, Vitest
- Packaging: Docker Compose
- Hosting: Vercel project (hono), Vercel Functions
- Code: 671 lines in 17 files (TypeScript 638, JSON 73, Markdown 47, Shell 33, YAML 11)
- Dependencies: 10 npm, 0 Python
- Deploy config: `docker-compose.yml`

### Stack fit

**62/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

STACK.md's choice of Hono on Vercel Functions with Neon Postgres is well reasoned and fits Vercel. The build departed from it in production by falling back to Runtime Cache because the Neon terms needed browser acceptance, so the live app doesn't meet the durable-storage requirement until the database is connected.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 5/10 | Hono with TypeScript and a Postgres design with atomic rate-limit counters fits the API well, but what is live stores persistent notes in Runtime Cache, which isn't a durable database and can't count atomically. |
| Proportion | 30 | 6/10 | The intended stack is lean (Hono, pg, hand-written OpenAPI), but the live store is a cache standing in for a database, kept as a second backend, and @vercel/blob is still an unused dependency. |
| Platform fit | 30 | 8/10 | Zero-config Hono on Vercel Functions with Fluid compute and a Marketplace Postgres plan suits the platform. The Runtime Cache fallback uses a platform feature for a job it isn't built for. |

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: In a browser, accept the Neon Marketplace terms for team ai-deploy-bench at https://vercel.com/ai-deploy-bench/~/integra; > Installing Neon by Neon under ai-deploy-bench { "status": "action_required", "reason": "integration_terms_acceptance_r

## Security and compliance review

**80/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.43) of the process, the code, the hosting plan and the live app.

The Notes API runs as a Hono function on Vercel Hobby, and secrets were handled cleanly: API_KEYS is a sensitive env var, nothing leaked into the uploaded files, and HTTPS, auth, validation and ownership checks all work with nothing extra exposed. The main weakness is storage: no Marketplace database could be installed, so production keeps notes in Vercel Runtime Cache, which can evict entries and has no atomic operations. That gives no durability guarantee, allows lost updates and lets the rate limit leak under bursts. Smaller issues are an unpinned `vercel@latest` CLI, CLI-upload deploys and missing app-level security headers.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS was piped from the environment into a sensitive Vercel production env var without being echoed, the Vercel token was only ever expanded from $VERCEL_TOKEN, and .env/.env*.local (including the CLI-generated VERCEL_OIDC_TOKEN file) are excluded from the upload. The only nit is a throwaway local Postgres password committed in docker-compose.yml. |
| Deployment provenance | 20 | 7/10 | Vercel builds the uploaded local sources with a package-lock.json present, so what runs matches the reviewed code, but deploys come from a CLI upload rather than a tracked repo, and the CLI is fetched unpinned as `npx -y vercel@latest` (also in scripts/deploy.sh), with caret dependency ranges. |
| Terms compliance | 15 | 6/10 | Hobby suits a personal side project, but the app's persistence depends on Vercel Runtime Cache, which Vercel offers as an evictable cache with no durability guarantee (and on Hobby it is shared with every project on the team), not as a database. That fails the task's 'survives restarts and redeploys' requirement as a platform guarantee. |
| Least privilege | 15 | 8/10 | Only one function and an implicit cache namespace exist, preview deployments are protected, and the production domain is public as the API needs. The dormant Postgres path turns off TLS certificate verification (rejectUnauthorized:false), and the cache namespace sits in team-shared storage. |
| Transport security | 10 | 9/10 | HTTP redirects with 308 to HTTPS, and the certificate is valid with platform HSTS (max-age 63072000, preload). The app sets no X-Content-Type-Options, frame protection or CSP on its /docs HTML, though Hono's secureHeaders or vercel.json headers could have added them. |
| Attack surface | 10 | 10/10 | Probes of /.env, /.git/config, /package.json, /src/app.ts and /.vercel/project.json all returned JSON 404s, errors are generic, and the only unauthenticated endpoints are the required /health, /openapi.json and /docs. |
| Application security | 5 | 6/10 | Input validation, auth and per-key ownership (404 for other keys) are correct, with no injection or XSS paths. But the active cache backend has a lost-update race on concurrent writes, the per-key rate limit lets extra requests through under bursts (72/80 in the agent's own test), each authenticated request triggers 32 cache reads, and title, content, tags and note counts are unbounded. |

Findings:

- **high** · deployment · Notes stored in Vercel Runtime Cache instead of a durable database: app/src/store.ts:178-179 `store()` falls back to cacheStore when DATABASE_URL is unset (it is unset in production); process/deployment.json notes: 'Runtime Cache is not a durable database: entries can be evicted under storage pressure (on Hobby the cache is shared by all projects on the team)'; ttl ONE_YEAR at store.ts:115 Fix: Finish the documented human step (accept Neon terms and install the integration) so DATABASE_URL is injected and the Postgres store is used, or use another real database; don't treat the cache as primary storage.
- **medium** · app · Lost updates on concurrent writes in the cache store: app/src/store.ts:131-137 `mutate` does load, modify and save of the whole per-owner array under an in-process lock only; deployment.json: 'two concurrent writes for the same API key on different instances can lose one update' Fix: Use a store with atomic writes or transactions (the existing Postgres path), or store one cache entry per note with an index that tolerates races.
- **medium** · app · Per-key rate limit is not enforced exactly under concurrency and amplifies backend reads: app/src/store.ts:144-158 sharded counter reads 32 slots per request; process/deploy.md final burst test: '72 200 / 8 429' for 80 concurrent requests on one key Fix: Use an atomic counter (Postgres INSERT ... ON CONFLICT, already in pgStore, or Redis INCR) so 60/min is strict and each request costs one round trip.
- **low** · app · No size limits on note fields, tags or note count: app/src/app.ts:39-62 `validate` checks only types and non-empty title; all of a key's notes are kept in one cache value (store.ts:113-116), so a large note or many notes could exceed cache item limits and make that key's notes fail Fix: Cap title, content and tag lengths, cap the number of tags and notes per key, and limit request body size (e.g. Hono bodyLimit).
- **low** · deployment · Unpinned deploy tooling and CLI upload instead of a tracked source: app/scripts/deploy.sh:10 `npx -y vercel@latest`; process/deploy.md: every deploy is `vercel deploy --prod --yes` from the local directory; package.json uses ^ ranges (a lockfile is uploaded) Fix: Pin the Vercel CLI version and deploy from a Git repository connected to the project, so each production build maps to a commit.
- **low** · app · Postgres TLS certificate verification disabled: app/src/db.ts:36 `ssl: ... { rejectUnauthorized: false }` for any non-local DATABASE_URL Fix: Keep certificate verification on (Neon presents publicly trusted certificates); use `ssl: true` or sslmode=verify-full.
- **low** · app · Missing security headers on /docs HTML and API responses: curl -sI https://adb-cy3y5-api.vercel.app/docs returns only strict-transport-security from the platform; no X-Content-Type-Options, X-Frame-Options/frame-ancestors or Content-Security-Policy Fix: Add Hono's secureHeaders middleware or a headers block in vercel.json.
- **info** · app · Hard-coded local development database password: app/docker-compose.yml:5 `POSTGRES_PASSWORD: notes` (local-only container, excluded from the upload by .vercelignore) Fix: Read it from an untracked .env file to set a good example; no production impact.
- **info** · app · Raw API key would be stored as note owner in Postgres: app/src/store.ts:63 inserts `owner` (the API key) unhashed, while the cache path hashes it (store.ts:113) Fix: Store a SHA-256 of the key as owner in Postgres too, so a database leak doesn't expose usable keys.

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
| POST /v1/notes creates a note | yes | passed |  |
| Invalid notes are rejected with 400 | yes | passed |  |
| GET /v1/notes/{id} returns the note | yes | passed |  |
| GET /v1/notes lists notes and filters by tag | yes | passed |  |
| Notes are listed newest first | no | passed |  |
| PATCH /v1/notes/{id} updates only the given fields | yes | passed |  |
| Notes are private to the API key that created them | yes | passed |  |
| DELETE /v1/notes/{id} removes the note | yes | passed |  |
| Notes are still there a minute later | yes | passed |  |
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
| project | adb-cy3y5-api | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The API is live at **https://adb-cy3y5-api.vercel.app** and every requirement in `TASK.md` passes there. The exception: notes aren't in a real database yet, because connecting one needs a person to accept terms in a browser.
>
> **What's deployed:** the Hono app as one Vercel project, `adb-cy3y5-api`, on the free Hobby plan, at $0 a month. `API_KEYS` is set from `BENCH_API_KEYS` as a sensitive production variable.
>
> **Tested through the public URL:**
> - `/health`, `/openapi.json` and `/docs` return 200.
> - A missing or unknown key gets 401.
> - Create, get, update and delete work; tag filtering and newest-first listing work.
> - Bad bodies get 400, and other keys get 404 on someone else's note.
> - After 60 requests a minute a key gets 429 with `Retry-After` and a JSON error, while the other key keeps getting 200.
>
> **What didn't work:**
> - **No Postgres.** Every Vercel Marketplace database (Neon, Supabase, Prisma Postgres, Upstash) refused to install until someone accepts its terms in a browser. That's the one entry in `human_steps`.
> - **No Vercel Blob either.** Creating a store was refused because this team had already used up its Hobby Blob allowance.
> - **Notes are in Vercel Runtime Cache instead.** It's a regional cache shared by all instances. A test note survived five production redeploys, but it isn't a durable database. Entries can be evicted when the cache fills up, and on Hobby that cache is shared with every other project on the team. Two simultaneous writes for the same key can also lose one update.
> - **The rate limit leaks under heavy bursts.** It's exact for one-at-a-time traffic and for 5 parallel requests. With 20 in parallel, 72 of 80 got through instead of 60, because the cache can't increment a counter atomically.
> - **Vercel's firewall rate limiting didn't help.** On Hobby it puts every API key in one shared bucket, so I removed it.
>
> **To fix both limitations:** someone opens https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon?source=cli and accepts the terms, then runs `scripts/deploy.sh`. That installs the free Neon database, and the app switches to Postgres with no code change, which makes storage durable and the rate limit exact.
>
> `deployment.json`, `README.md` and `STACK.md` record these details, and `scripts/smoke.sh` re-runs the checks. No secrets were printed or written to committed or deployed files. `vercel link` created a short-lived OIDC token in `.env.local`, which is excluded from both git and uploads. The local Postgres container is stopped.

## Shell commands during deploy

- `3s` `export V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V whoami 2>&1 | tail -1; $V projects ls 2>&1 | tail -5; $V integration list 2>&1 | tail -5`
- `11s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V link --yes --project adb-cy3y5-api 2>&1 | tail -3; cat .vercel/project.json; echo; $V integration add --help 2>&1 | sed -n 1,`
- `17s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration add neon --help 2>&1 | grep -iA30 -E 'plan|metadata' | head -50`
- `21s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration add neon --name adb-cy3y5-api-db --plan free 2>&1 | grep -v -iE 'postgres(ql)?://' | tail -20`
- `30s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration installations 2>&1 | tail -10; for i in upstash supabase prisma; do echo "== $i"; $V integration add $i --name ad`
- `50s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v2/teams/$VERCEL_TEAM_ID" | node -pe 'const t=JSON.parse(require("fs").readFileSync(0)); JSON.stringify({plan:t.billing?.plan, `
- `1m 20s` `npm i @vercel/blob@latest @vercel/functions@latest 2>&1 | tail -1; node -p 'require("./node_modules/@vercel/blob/package.json").version+" "+require("./node_modules/@vercel/functions/package.json").ver`
- `1m 24s` `sed -n 100,135p node_modules/@vercel/blob/dist/index.d.ts; sed -n 170,200p node_modules/@vercel/blob/dist/index.d.ts; grep -rn "getCache\|interface RuntimeCache" node_modules/@vercel/functions/*.d.ts `
- `1m 28s` `cat node_modules/@vercel/functions/cache/*.d.ts | head -80`
- `1m 44s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V blob create-store --help 2>&1 | sed -n '/Options/,/Global/p'; sed -n 133,160p node_modules/@vercel/blob/dist/index.d.ts; grep`
- `1m 48s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V blob create-store adb-cy3y5-api-blob --access private --yes 2>&1 | grep -viE 'token|secret' | tail -6; $V env ls 2>&1 | tail `
- `1m 54s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V blob list-stores --all 2>&1 | tail -5; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v1/edge-confi`
- `2m 34s` `cat > src/store.ts <<'EOF'`
- `2m 40s` `python3 - <<'EOF'`
- `2m 50s` `docker compose stop >/dev/null 2>&1; V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"`
- `3m 10s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V deploy --prod --yes > /tmp/dep.log 2>&1; grep -vE 'token' /tmp/dep.log | head -40`
- `3m 25s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; echo "keys: $(echo "$BENCH_API_KEYS" | tr , '\n' | wc -l)"; curl -s https://adb-cy3y5-api.vercel.app/health; echo; BASE=https://adb-cy3y5-api.vercel.app KE`
- `3m 51s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; timeout 40 $V logs https://adb-cy3y5-api.vercel.app 2>&1 | grep -v token | head -30`
- `3m 59s` `printf '\n// Vercel picks src/app.ts as the Hono entrypoint, so default-export the app here too.\nexport default app;\n' >> src/app.ts && npx tsc && V="npx -y vercel@latest --token $VERCEL_TOKEN --sco`
- `4m 28s` ❌ `sleep 60; IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `4m 34s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `4m 55s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `5m 00s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `5m 22s` `npm i @vercel/firewall@latest 2>&1 | tail -1; ls node_modules/@vercel/firewall/dist; cat node_modules/@vercel/firewall/dist/index.js | head -150`
- `5m 26s` `sed -n '/var rate_limit_exports/,$p' node_modules/@vercel/firewall/dist/rate-limit.js | head -150`
- `5m 33s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall --help 2>&1 | sed -n 1,40p`
- `5m 36s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall rules add --help 2>&1 | sed -n '/Options/,/Global/p;/Examples/,$p' | head -90`
- `5m 42s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall rules add adb-cy3y5-api-ratelimit --description "60 req/min per API key via @vercel/firewall checkRateLimit" --condi`
- `5m 57s` `python3 - <<'EOF'`
- `6m 14s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `7m 04s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; timeout 40 $V logs --deployment adb-cy3y5-api.vercel.app 2>&1 | grep -v token | node -e 'for (const l of require("fs").readFileS`
- `7m 12s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; timeout 40 $V logs --help 2>&1 | grep -E '^\s+-' | head -20; timeout 40 $V logs --deployment adb-cy3y5-api.vercel.app --since 10`
- `7m 23s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v1/security/firewall/config/active?projectId=prj_O474eacqKPTkYckg4skGKfKIyPbl&teamId=$VERCEL_TEAM_ID" | node -pe 'JSON.stringif`
- `7m 29s` `for i in $(seq 1 65); do curl -s -o /dev/null -w '%{http_code}\n' -H 'x-vercel-rate-limit-api: adb-cy3y5-api-notes' -H 'x-vercel-rate-limit-key: probe-abc' -H 'user-agent: Bot/Vercel Rate Limit Checke`
- `7m 43s` `python3 - <<'EOF'`
- `8m 03s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; B=https://adb-cy3y5-api.vercel.app`
- `9m 08s` `cp src/app.ts /tmp/app.ts.bak && python3 - <<'EOF'`
- `9m 26s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; curl -s -D - -o /dev/null -H "X-API-Key: $K2" https://adb-cy3y5-api.vercel.app/v1/notes; cat .vercelignore`
- `9m 36s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; for i in $(seq 1 65); do curl -s -D - -o /dev/null -H "X-API-Key: $K2" https://adb-cy3y5-api.ver`
- `10m 10s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; seq 1 80 | xargs -P 20 -I{} sh -c "curl -s -D - -o /dev/null -H 'X-API-Key: $K1' https://adb-cy3`
- `11m 06s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; seq 1 80 | xargs -P 20 -I{} curl -s -o /dev/null -w '%{http_code}\n' -H "X-API-Key: $K1" https:/`
- `12m 08s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall rules edit --help 2>&1 | grep -E '^\s+--' | head -20`
- `12m 14s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall rules edit adb-cy3y5-api-ratelimit --rate-limit-keys ja4 --yes 2>&1 | tail -2; $V firewall publish --yes 2>&1 | tail`
- `13m 03s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V firewall rules update adb-cy3y5-api-ratelimit --rate-limit-keys ja4 --rate-limit-requests 60 --rate-limit-window 60 --yes 2>&`
- `13m 13s` `Q="projectId=prj_O474eacqKPTkYckg4skGKfKIyPbl&teamId=$VERCEL_TEAM_ID"; RULE=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v1/security/firewall/config/active?$Q" | node -pe`
- `13m 19s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; seq 1 80 | xargs -P 20 -I{} curl -s -o /dev/null -w '%{http_code}\n' -H "X-API-Key: $K1" https:/`
- `14m 16s` `Q="projectId=prj_O474eacqKPTkYckg4skGKfKIyPbl&teamId=$VERCEL_TEAM_ID"; curl -s -X PATCH -H "Authorization: Bearer $VERCEL_TOKEN" -H 'Content-Type: application/json' -d '{"action":"rules.remove","id":"`
- `14m 34s` `cp /tmp/app.ts.bak src/app.ts && python3 - <<'EOF'`
- `14m 41s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V deploy --prod --yes 2>&1 | grep -E '"readyState"|Error'; IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s)`
- `15m 06s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; seq 1 70 | xargs -P 5 -I{} curl -s -o /dev/null -w '%{http_code}\n' -H "X-API-Key: $K1" https://`
- `16m 12s` `IFS=, read -r K1 K2 _ <<< "$BENCH_API_KEYS"; until [ $(( $(date +%s) % 60 )) -lt 3 ]; do sleep 1; done; BASE=https://adb-cy3y5-api.vercel.app KEY1="$K1" KEY2="$K2" scripts/smoke.sh; B=https://adb-cy3y`
- `17m 21s` `cat > scripts/deploy.sh <<'EOF'`
- `17m 35s` `cat > deployment.json <<'EOF'`
