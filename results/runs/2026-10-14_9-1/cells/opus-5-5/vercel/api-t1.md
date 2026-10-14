# ✅ API / Backend Service on Vercel with Opus 5.5 (trial 1)

**success**: 20/20 checks passed (100%).

- URL: https://adb-yz96j-api.vercel.app (from deployment.json)
- Estimated hosting: Light use: $0.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-yz96j-api`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 22s | 4m 51s | 7m 12s |
| Turns | 11 | 23 | |
| Tokens | 465.3K | 1.55M | 2.02M |
| Agent cost | $0.52 | $0.81 | $1.33 |
| Shell commands | 10 | 22 | |

App answered 0s after the agent finished deploying.

## Screenshots

**The API documentation at /docs** (https://adb-yz96j-api.vercel.app/docs)

![The API documentation at /docs](api-t1/docs.jpg)

## What was built

- Stack: `@vercel/blob`, `hono`, `pg`
- Code: 652 lines in 15 files (JavaScript 652, JSON 40, Markdown 14)
- Dependencies: 4 npm, 0 Python
- Deploy config: `vercel.json`

## Human steps

2 step(s), about 5 min of a person's time.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup

Reported but not needed, since the deployment worked without them: Optional: accept the Neon marketplace terms for team ai-deploy-bench at https://vercel.com/ai-deploy-bench/~/integration; api"} > Installing Neon by Neon under ai-deploy-bench { "status": "action_required", "reason": "integration_terms_accept

## Security and compliance review

**82/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.42) of the process, the code, the hosting plan and the live app.

The Notes API is cleanly built on Vercel: secrets live in project env vars and stay out of the upload, the Blob store is private, ownership and validation work, and probes found no exposed files, stack traces or debug endpoints. The main weakness is fit: every authenticated request writes to Vercel Blob for rate limiting, so the Hobby plan's small free operations allowance could run out and take the API down. Hobby itself is appropriate for this personal project. Smaller gaps: no app-set security headers, no field size limits, a local CLI upload instead of a git-backed deploy, and the Blob token stored as a non-sensitive variable.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 9/10 | API_KEYS was piped from the environment into a Vercel Secret-type env var and BLOB_READ_WRITE_TOKEN came from the store connection. Nothing is hard-coded, and .env/.env.local are kept out of the upload by .vercelignore. Minor issues: the Blob token is a plain 'Config' env var whose prefix was printed by `vercel env ls`, and the Vercel token was passed as a command-line argument. |
| Deployment provenance | 20 | 8/10 | The code was deployed straight from the agent's working directory with `vercel deploy --prod`. The committed package-lock.json pins dependencies, and the build ran on Vercel's builder. There's no git-backed source of record, the global CLI was installed as `vercel@latest`, and `engines.node` is an open `>=20` range. |
| Terms compliance | 15 | 6/10 | Vercel Hobby allows personal, non-commercial use, so the plan fits this personal project. The app writes to Vercel Blob on every authenticated request, though: each request updates the rate-limit counter. Hobby's included Blob operations (about 2k advanced operations a month, by my understanding, and the agent says the same) could run out after a few thousand requests, and Hobby blocks usage once the free allowance is gone. The agent disclosed this. |
| Least privilege | 15 | 9/10 | The Blob store was created with private access, and reads and writes use access:'private'. Owner data is keyed by a SHA-256 hash of the API key. The only resources are one serverless function and one store. The read-write token covers the whole store and is also exposed to the Development environment. |
| Transport security | 10 | 8/10 | HTTP returns a 308 redirect to HTTPS, the certificate is valid, and the platform adds HSTS with preload. The agent didn't add X-Content-Type-Options, frame protection or CSP, which it could have set in vercel.json. |
| Attack surface | 10 | 9/10 | Every path is rewritten to the Hono app, so /.env, /.git/config, /package.json, the source files and /.vercel return a JSON 404, and errors are generic with no stack traces. Only the platform's /_src redirect remains, and it requires a Vercel login. |
| Application security | 5 | 7/10 | Input is type-checked, ownership is enforced by storage path (other keys get 404), IDs are UUID-validated, and per-key rate limiting uses compare-and-swap. There are no length or count limits on title, content or tags. One key's notes live in a single document that keeps growing, and rate-limit blobs are never cleaned up. |

Findings:

- **medium** · deployment · Free Blob quota can be exhausted by normal use, taking the API down: app/src/store/blob.js:77-88: store.hit() calls put() on every authenticated /v1 request; app/src/app.js:85. process/deployment.json notes: 'The Hobby free allowance (about 2k advanced operations a month) suits light personal use'. process/context.json: team plan 'hobby'. Fix: Keep rate-limit counters out of Blob, for example in Upstash Redis/KV (Marketplace) or Postgres. Or move to a plan with metered Blob usage so normal traffic can't block the store.
- **low** · app · No size limits on note fields, and per-key notes stored in one growing document: app/src/app.js:31-50 checks only types and non-empty title, with no maximum length for title, content or tags. app/src/store/blob.js:90-97 appends every note to a single notes/<owner>.json document that is read in full on each request. Fix: Cap title, content, tag length and tag count. Reject oversized bodies early. Consider storing one blob per note or using a real database.
- **low** · app · Rate-limit blobs accumulate indefinitely: app/src/store/blob.js:81 writes ratelimit/<owner>/<window>.json each minute a key is used, and nothing deletes them (the Postgres store prunes them; pg.js has a DELETE of old windows). Fix: Delete expired windows, or use a store with a TTL.
- **low** · deployment · No app-level security headers: curl -sI https://adb-yz96j-api.vercel.app/docs: only strict-transport-security is present, with no x-content-type-options, x-frame-options/frame-ancestors or content-security-policy. Fix: Add a `headers` block in vercel.json, or Hono's secureHeaders middleware, to set nosniff, frame-ancestors 'none' and a restrictive CSP.
- **low** · deployment · Blob token stored as a non-sensitive env var, with its prefix shown in the log: process/deploy.md:298 and :503: `BLOB_READ_WRITE_TOKEN eyJ2IjoidjIiLCJjIj… Config Production, Preview, Development`. The Vercel token was passed via `--token $VERCEL_TOKEN` on many commands (e.g. deploy.md:478). Fix: Mark the Blob token as a sensitive env var and limit it to Production/Preview. Pass the Vercel token through the VERCEL_TOKEN env var rather than argv.
- **low** · deployment · Local CLI upload with an unpinned CLI and Node major: process/deploy.md:4 `npm i -g vercel@latest`. deploy.md:478 `vercel deploy --prod` from the working directory. The build log warns that `"engines": { "node": ">=20" }` will auto-upgrade. Fix: Deploy from a git repository the owner controls, pin the CLI version, and pin engines.node to a single major (e.g. "22.x").
- **info** · platform · Platform /_src redirect: GET https://adb-yz96j-api.vercel.app/_src returns 307 to vercel.com/deployments/.../source, which returns 302 to the login page. Fix: No action needed. Keep Vercel's source protection on.
- **info** · app · Unauthenticated requests are not rate limited: app/src/app.js:79-85: the invalid-key 401 is returned before store.hit(). They cost no storage operations, but invalid keys can be guessed without limit (keys come from the operator). Fix: Consider an IP-based limit on failed auth (e.g. Vercel Firewall rate limiting), and issue long random keys.

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
| project | adb-yz96j-api | — | $0.00 | no fixed fee; usage within the plan's included allowance |
| blob_store | adb-yz96j-api-blob | — | $0.00 | usage-billed; free within plan allowance |

Teardown: 2 deleted

## Agent's deploy summary

> The Notes API is live at **https://adb-yz96j-api.vercel.app** and every requirement in `TASK.md` works through that URL. It costs $0 a month on the Hobby plan.
>
> **What's deployed:**
> - **Vercel project `adb-yz96j-api`:** the Hono app runs as a single Node.js function in the `iad1` (Washington, D.C.) region.
> - **API keys:** `API_KEYS` is set to exactly the two keys in `BENCH_API_KEYS`, for production and preview.
> - **Storage, private Vercel Blob store `adb-yz96j-api-blob`:** Postgres wasn't possible. Installing Neon from the Vercel Marketplace requires someone to accept its terms in a browser, so I used Blob, which is Vercel's own product.
>   - Each key's notes are one JSON document.
>   - Every write only succeeds if nothing else changed the document first, so simultaneous requests can't lose updates.
>   - Rate-limit counts are stored the same way, so the 60-per-minute limit holds across all running copies of the function.
> - **Postgres switch:** if `DATABASE_URL` is set later, the app uses Postgres automatically.
>
> **What I tested through the public URL:**
> - `/health`, `/docs` and `/openapi.json` respond without a key.
> - Missing or wrong keys get `401`.
> - Create, get, list with the `tag` filter, update and delete all work.
> - Bad input gets `400` (empty title, tags not an array of strings, wrong types).
> - The second key gets `404` on the first key's note for get, update and delete.
> - **Rate limiting:** I sent 65 requests at once on one key, and with the earlier test traffic exactly 60 were allowed in that minute. The rest got `429` with `Retry-After` and a JSON error, while the other key still got `200`. The limited key worked again once the minute passed.
>
> **Limitations:**
> - **Free Blob allowance:** every write and every rate-limit count uses up Blob operations. The free allowance (roughly 2,000 a month, from memory, not checked) is enough for a few friends' scripts but not for heavy traffic.
> - **Speed:** requests take about 100–300 ms.
> - **Large note counts:** keeping all of a key's notes in one document is fine for personal use but would slow down with very large numbers of notes.
>
> **Optional human step:** if you want Neon Postgres instead of Blob, someone needs to accept the Neon terms at https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon, then run `vercel integration add neon --name adb-yz96j-api-db` and redeploy. This is listed in `deployment.json` as non-blocking.
>
> The Blob token is saved in `.env`, which `.vercelignore` keeps out of the deployment. I printed no secrets and stopped the local database container.

## Shell commands during deploy

- `4s` `npm i -g vercel@latest >/dev/null 2>&1; vercel --version; echo "BENCH keys count: $(echo $BENCH_API_KEYS | tr ',' '\n' | wc -l)"; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.c`
- `18s` `vercel integration --help 2>&1 | head -40; vercel integration add --help 2>&1 | head -40`
- `24s` `export VERCEL_ORG_ID=$VERCEL_TEAM_ID; vercel link --yes --project adb-yz96j-api --scope $VERCEL_TEAM_ID --token $VERCEL_TOKEN 2>&1 | tail -3; cat .vercel/project.json; echo; vercel integration add neo`
- `39s` `curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v2/teams/$VERCEL_TEAM_ID" | node -pe 'const t=JSON.parse(require("fs").readFileSync(0));JSON.stringify({plan:t.billing?.plan, s`
- `44s` `mkdir -p /tmp/blobpkg && cd /tmp/blobpkg && npm pack @vercel/blob@2.8.1 >/dev/null 2>&1 && tar xzf vercel-blob-2.8.1.tgz && ls package/dist && grep -n "ifMatch\|allowOverwrite\|access\b\|'private'\|Bl`
- `58s` `sed -n 180,300p /tmp/blobpkg/package/dist/index.d.ts; grep -n "BlobNotFoundError\|class Blob.*Error\|^export" /tmp/blobpkg/package/dist/index.d.ts | head -30`
- `1m 01s` `vercel blob create-store --help --token $VERCEL_TOKEN 2>&1 | sed -n 5,30p`
- `1m 04s` `vercel blob create-store adb-yz96j-api-blob --access private --yes --scope $VERCEL_TEAM_ID --token $VERCEL_TOKEN 2>&1 </dev/null | grep -v -i token | tail -8; vercel env ls --scope $VERCEL_TEAM_ID --t`
- `1m 08s` `vercel env ls --scope $VERCEL_TEAM_ID --token $VERCEL_TOKEN 2>&1 | grep -E "^\s+[A-Z_]+" ; sed 's/=.*/=<redacted>/' .env.local`
- `1m 19s` `grep -n "GetBlobResultBlobBase" -A 25 /tmp/blobpkg/package/dist/index.d.ts | sed -n 1,30p; grep -n "interface PutBlobResult" -A 12 /tmp/blobpkg/package/dist/*.d.ts | head -20`
- `1m 47s` `npm i @vercel/blob >/dev/null 2>&1 && mkdir -p src/store && git mv 2>/dev/null; mv src/db.js src/store/pg-pool.js && cat > src/store/pg.js <<'EOF'`
- `2m 02s` `cat > src/store/index.js <<'EOF'`
- `2m 10s` `python3 - <<'EOF'`
- `2m 32s` `set -a; . ./.env.local; set +a; export API_KEYS=cas-$(date +%s); cat > /tmp/cas.mjs <<'EOF'`
- `2m 41s` `sed -i 's#/already exists|precondition|etag/i#/already exists|precondition|etag|conflict/i#' src/store/blob.js && set -a; . ./.env.local; set +a; export API_KEYS=cas2-$(date +%s); node /tmp/cas.mjs & `
- `2m 54s` `grep BLOB_READ_WRITE_TOKEN .env.local > .env && chmod 600 .env && printf '.env\n.env.*\n.vercel\nnode_modules\ntest\ndeployment.json\n' > .vercelignore && cat > vercel.json <<'EOF'`
- `3m 19s` `vercel env ls --scope $VERCEL_TEAM_ID --token $VERCEL_TOKEN 2>&1 | grep -E "^\s+[A-Z_]+"; vercel deploy --prod --yes --scope $VERCEL_TEAM_ID --token $VERCEL_TOKEN 2>&1 | grep -vi "token" | head -40`
- `3m 42s` `B=https://adb-yz96j-api.vercel.app; for p in /health /docs /openapi.json /v1/notes; do curl -s -o /tmp/o -w "$p %{http_code} " $B$p; head -c 120 /tmp/o; echo; done`
- `3m 49s` `B=https://adb-yz96j-api.vercel.app; K1=$(echo $BENCH_API_KEYS | cut -d, -f1); K2=$(echo $BENCH_API_KEYS | cut -d, -f2)`
- `3m 58s` `B=https://adb-yz96j-api.vercel.app; K1=$(echo $BENCH_API_KEYS | cut -d, -f1); K2=$(echo $BENCH_API_KEYS | cut -d, -f2)`
- `4m 17s` `docker rm -f notes-pg >/dev/null && python3 - <<'EOF'`
- `4m 21s` `sleep 20; K1=$(echo $BENCH_API_KEYS | cut -d, -f1); curl -s -o /dev/null -w "%{http_code}\n" https://adb-yz96j-api.vercel.app/v1/notes -H "X-API-Key: $K1"`
