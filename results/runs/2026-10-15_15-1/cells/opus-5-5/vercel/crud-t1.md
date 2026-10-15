# ⚠️ Database-Backed CRUD App on Vercel with Opus 5.5 (trial 1)

**partial** (failed at human): 5/19 checks passed (26%).

- URL: https://adb-xpnab-crud-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-xpnab-crud`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 03s | 1m 41s | 6m 03s |
| Turns | 8 | 10 | |
| Tokens | 320.8K | 640.4K | 1.73M |
| Agent cost | $0.41 | $0.27 | $1.07 |
| Shell commands | 7 | 9 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 2m 19s, 769.3K tokens, $0.40).

## Screenshots

**The web app before signing in** (https://adb-xpnab-crud-web.vercel.app/)

![The web app before signing in](crud-t1/signin.jpg)

## What was built

- Runtime: Node.js
- Frameworks: Express
- Libraries: node-postgres, bcrypt.js
- Packaging: vercel.json
- Hosting: Vercel project, Vercel Functions
- Code: 406 lines in 15 files (JavaScript 235, HTML 123, Shell 48, JSON 43, Markdown 32)
- Dependencies: 3 npm, 0 Python
- Deploy config: `vercel.json`

### Stack fit

**83/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

A lean, well-reasoned stack (Express on Vercel Functions, Neon Postgres, static UI) that fits a multi-user todo app and uses Vercel's strengths. The weak point was carrying it out: the Marketplace database was never provisioned.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 8/10 | Express with pg against managed Postgres, bcryptjs and a static HTML page covers every requirement: durable storage, a slow password hash and a simple UI. STACK.md rightly rules out SQLite on Vercel's ephemeral disk, and the agent refused to use Blob or Edge Config as a stand-in database. The build departed from the plan only in that the database was never created. |
| Proportion | 30 | 9/10 | There are only three runtime dependencies and no build step, frontend framework or extra services. Using database-backed opaque tokens means there is no JWT signing secret to manage. |
| Platform fit | 30 | 8/10 | Express runs as a single Vercel Function and the UI is served from the CDN, which is how Vercel is meant to be used. A pg.Pool inside serverless functions needs Neon's pooled connection string (or its serverless driver) to avoid exhausting connections, and the code doesn't do anything specific to ensure that. |

## Human steps

3 step(s), about 8 min of a person's time. **Blocked:** the deploy couldn't finish without them.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup; agent: Run scripts/deploy.sh (it uses VERCEL_TOKEN and VERCEL_TEAM_ID from the environment or .env). (Creates Neon Postgres adb-xpnab-crud-db (free plan, iad1), connects it to adb-xpnab-crud-web (sets DATABASE_URL/POSTGRES_URL), redeploys to production, and runs scripts/smoke.sh (23 checks covering every T
- **Install a Marketplace integration and accept its terms in a browser** (~3 min): agent: Open https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon?source=cli while logged in to the ai-deploy-bench team and accept the Neon Marketplace terms. (`vercel integration add neon` returned status action_required / integration_terms_acceptance_required, which only a person can compl; tool output: > Installing Neon by Neon under ai-deploy-bench { "status": "action_required",

## Security and compliance review

**69/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.36) of the process, the code, the hosting plan and the live app.

The code itself is well built: parameterized SQL, bcrypt, hashed opaque tokens, per-user scoping, nothing exposed, and HTTPS with HSTS. But the production API doesn't work: no database was ever provisioned, so every /api call returns 503. The biggest compliance problem is that a commercial app was deployed on Vercel's non-commercial Hobby plan without flagging it. Smaller issues are a plaintext deploy token in the project folder, unpinned CLI tooling, no rate limiting, and Postgres TLS verification turned off.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 8/10 | No credentials appear in source, deployed files or the live site, and the app reads DATABASE_URL/POSTGRES_URL from the environment, which the Vercel Marketplace integration would set. The agent did write the Vercel token to a plaintext .env in the project folder and passed it as a --token argument on every CLI call. .vercelignore and .gitignore kept the file out of the upload. |
| Deployment provenance | 20 | 7/10 | Production runs the code the agent built, uploaded from its local directory with the Vercel CLI. A package-lock.json pins the npm dependencies. But there is no git-backed source the owner controls, and the CLI ran unpinned as `npx -y vercel@latest`. |
| Terms compliance | 15 | 2/10 | context.json says this is a commercial app, but the team is on Vercel's Hobby plan, which Vercel's terms limit to personal, non-commercial use. The agent called it 'Hobby-tier usage' and never raised the conflict. The free Neon database it planned also scales to zero. |
| Least privilege | 15 | 8/10 | Only the function and the static assets are public, and the per-deployment URL sits behind Vercel deployment protection (302 to login). No data store exists yet. As designed, the app would use the integration's owner-level connection string and run DDL on its first request, not a narrower runtime role. |
| Transport security | 10 | 8/10 | The app is served only over HTTPS with a valid certificate. Plain HTTP gets a 308 redirect to HTTPS, and the platform adds HSTS with preload. X-Content-Type-Options, frame protection and CSP are all missing, though the agent could have set them with a `headers` block in vercel.json. |
| Attack surface | 10 | 9/10 | Probes for /.env, /.git/config, package.json, source files, vercel.json and .vercel/ all return the platform 404. The API returns generic JSON errors with no stack traces. Only GET / and /api/* are reachable. |
| Application security | 5 | 6/10 | The code uses parameterized SQL, bcrypt (cost 10), random tokens stored as SHA-256 hashes, every todo query scoped to the owner, and textContent rendering, so it avoids XSS. However, login and signup have no rate limiting, sessions never expire, titles have no length cap, and the Postgres TLS connection skips certificate verification. Also, the live API doesn't work: every /api request returns 503. |

Findings:

- **high** · deployment · Commercial app deployed on a Vercel Hobby (non-commercial) plan: process/context.json: "use": "commercial", team_plans: "hobby"; process/deployment.json resource plan: "Vercel team's existing plan (Hobby-tier usage)". Vercel's Hobby plan is limited to personal, non-commercial use. Fix: Deploy to a Vercel Pro (or Enterprise) team, or flag the plan conflict to the owner as a blocking human step before going live.
- **medium** · deployment · No database provisioned; the whole API returns 503 in production: GET /api/todos -> 503 {"error":"database not configured"}; POST /api/auth/signup in deploy.md -> 503. Neon integration add failed with integration_terms_acceptance_required (process/deploy.md). Fix: Accept the Neon Marketplace terms (or attach another managed Postgres), set DATABASE_URL, redeploy, and run scripts/smoke.sh.
- **low** · deployment · Planned database is a free tier that scales to zero: process/deployment.json: Neon plan free_v3; scripts/deploy.sh line 13 `--plan free_v3`. Fix: For a business app, use a paid Neon or Postgres plan with an SLA and no cold-start or compute-hour limits.
- **low** · deployment · Vercel token stored in a plaintext .env and passed on the command line: process/deploy.md line 4: printf 'VERCEL_TOKEN=%s...' > .env; every call uses `npx -y vercel@latest --token $VERCEL_TOKEN`; scripts/deploy.sh lines 5-7 source .env and put the token in argv. Fix: Let the CLI read the VERCEL_TOKEN environment variable rather than putting it in --token, and don't keep the token on disk in the project directory.
- **low** · deployment · Unpinned deploy tooling and local-directory uploads: scripts/deploy.sh line 7: `npx -y vercel@latest`; deploys uploaded from the working directory with `vercel deploy --prod --yes`; dependencies use caret ranges in app/package.json, pinned only by the lockfile. Fix: Pin the Vercel CLI version and deploy from a git repository connected to the project so every production build can be traced to a commit.
- **low** · app · No rate limiting on login and signup, and sessions never expire: app/lib/app.js lines 48-74 (signup/login handlers have no throttling); sessions table (app/lib/db.js) has no expiry and auth() checks only that the hash exists. Fix: Add per-IP or per-account throttling (e.g. Vercel WAF rate limits or a counter in the database) and give session tokens a TTL.
- **low** · app · Postgres TLS certificate verification disabled: app/lib/db.js line 9: `ssl: local ? false : { rejectUnauthorized: false }`. Fix: Use `ssl: true` (or sslmode=require with verification) so connections to Neon verify the server certificate.
- **low** · deployment · Missing security headers the project could set: curl -sI https://adb-xpnab-crud-web.vercel.app/ shows strict-transport-security but no x-content-type-options, x-frame-options/frame-ancestors or content-security-policy; app/vercel.json has no headers block. Fix: Add a `headers` section in vercel.json setting X-Content-Type-Options: nosniff, a CSP with frame-ancestors 'none', and Referrer-Policy.
- **info** · app · Todo titles have no length limit: app/lib/app.js POST/PATCH /api/todos accept any non-empty string up to express.json's default 100 kB. Fix: Cap title length (e.g. 500 characters) and return 400 for anything longer.
- **info** · platform · Static assets served with Access-Control-Allow-Origin: *: curl -sI / -> access-control-allow-origin: * (Vercel CDN default for static files); API responses carry no CORS header. Fix: No action needed for a public HTML page.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the web app as HTML | yes | passed |  |
| POST /api/auth/signup creates an account and returns a token | yes | failed | POST /api/auth/signup returned 503, expected 201 or 200: {"error":"database not configured"} |
| Signup rejects an invalid email and a short password with 400 | yes | failed | invalid email: expected 400, got 503 |
| Signing up twice with the same email returns 409 | yes | failed | not run: depends on signup |
| POST /api/auth/login returns a token | yes | failed | not run: depends on signup |
| Login with a wrong password returns 401 | yes | failed | not run: depends on signup |
| /api/todos requires a valid token (401) | yes | failed | GET /api/todos returned 503, expected 401 or 403: {"error":"database not configured"} |
| POST /api/todos creates a todo | yes | failed | not run: depends on login |
| An empty title is rejected with 400 | yes | failed | not run: depends on login |
| GET /api/todos lists the caller's todos | yes | failed | not run: depends on create |
| Todos are listed oldest first | no | failed | not run: depends on create |
| PATCH /api/todos/{id} renames and completes a todo | yes | failed | not run: depends on create |
| Users can't see or modify each other's todos (404) | yes | failed | not run: depends on create |
| DELETE /api/todos/{id} removes a todo | yes | failed | not run: depends on create |
| Data is still there a minute later, with a fresh login | yes | failed | not run: depends on create |
| The web UI renders a login or signup form | no | passed |  |

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $0.00 of usage |
| Busy | $20.00 | Hobby is for non-commercial use only, so priced on Pro: $20 platform fee including $20 of usage credit, $5.75 of usage |

Each resource's list price, at the size it was provisioned and always on:

| Kind | Name | Plan | $/month | How it was priced |
|---|---|---|---|---|
| project | adb-xpnab-crud-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The app is deployed at **https://adb-xpnab-crud-web.vercel.app**, but the API doesn't work yet because there's no database.
>
> **Through the public URL:** I tested both. `GET /` returns the web UI (200, HTML) over HTTPS. Every `/api/*` endpoint returns `503 {"error":"database not configured"}`.
>
> **What blocked it:** creating the free Neon Postgres database (`adb-xpnab-crud-db`) failed with `integration_terms_acceptance_required`. Vercel only offers Postgres through Marketplace integrations, the team has none installed, and accepting Neon's terms has to be done by a person in a browser. I didn't use Vercel Blob or Edge Config instead: they aren't databases, and Blob's cached reads would show stale todos.
>
> **To finish (a person, about a minute):**
> 1. While logged in to the `ai-deploy-bench` team, open https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon?source=cli and accept the terms.
> 2. Run `scripts/deploy.sh`. It creates the database (free plan, `iad1`), connects it to the project, redeploys to production, and runs `scripts/smoke.sh`. Those 23 checks cover every requirement in `TASK.md`; locally they all pass, but they haven't run against Vercel yet.
>
> **Created so far:** the Vercel project `adb-xpnab-crud-web` (`prj_kv6kAE3Lq0RbzDegTCG3mNG5TtV8`), deployed to production. Expected cost is $0 a month.
>
> The credentials are saved in `.env`, which is excluded from deploys. `deployment.json` lists the URL, resources and the two human steps.

## Shell commands during deploy

- `4s` `printf 'VERCEL_TOKEN=%s\nVERCEL_TEAM_ID=%s\n' "$VERCEL_TOKEN" "$VERCEL_TEAM_ID" > .env && V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V whoami 2>&1 | tail -1; $V link --ye`
- `12s` `cat .vercel/project.json; echo; sed 's/=.*/=***/' .env.local; V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration add neon --help 2>&1 | sed -n '/Metadata\|Plans\|pl`
- `18s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration add neon --name adb-xpnab-crud-db --plan free_v3 -m region=iad1 -m auth=false --no-env-pull -e production -e prev`
- `26s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V integration installations 2>&1 | tail -15; $V integration list 2>&1 | tail -15; curl -s -H "Authorization: Bearer $VERCEL_TOK`
- `39s` `cat .vercelignore; V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V deploy --prod --yes 2>&1 | tail -6`
- `54s` `V="npx -y vercel@latest --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $V deploy --prod --yes 2>&1 | grep -v -i token | head -40`
- `1m 10s` `B=https://adb-xpnab-crud-web.vercel.app; curl -s -o /dev/null -w '/ %{http_code} %{content_type}\n' $B/; curl -s -w ' %{http_code}\n' $B/api/todos; curl -s -w ' %{http_code}\n' -XPOST $B/api/auth/sign`
- `1m 19s` `cat > scripts/deploy.sh <<'EOF'`
- `1m 34s` `cat > deployment.json <<'EOF'`
