# ⚠️ Database-Backed CRUD App on Vercel with Opus 5.5 (trial 1)

**partial** (failed at human): 5/19 checks passed (26%).

- URL: https://adb-72l2v-crud-web.vercel.app (from deployment.json)
- Estimated hosting: Light use: $20.00/month, Busy: $20.00/month (the agent estimated $0.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-72l2v-crud`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 2m 00s | 1m 29s | 4m 52s |
| Turns | 11 | 15 | |
| Tokens | 443.0K | 897.7K | 1.92M |
| Agent cost | $0.45 | $0.34 | $1.06 |
| Shell commands | 10 | 14 | |

App answered 0s after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 1m 23s, 577.4K tokens, $0.28).

## Screenshots

**The web app before signing in** (https://adb-72l2v-crud-web.vercel.app/)

![The web app before signing in](crud-t1/signin.jpg)

## What was built

- Runtime: Node.js 20+
- Frameworks: Express
- Libraries: node-postgres, bcrypt.js
- Packaging: vercel.json
- Hosting: Vercel project (express), Vercel Functions
- Code: 369 lines in 14 files (JavaScript 348, Markdown 42, JSON 38, Shell 21)
- Dependencies: 3 npm, 0 Python
- Deploy config: `vercel.json`

### Stack fit

**79/100**, from the same independent review, judged against the app's requirements rather than a preferred stack.

Node/Express as one Vercel Function backed by Neon Postgres is a proportionate, platform-appropriate stack, and STACK.md documents the choice well. The build followed that plan, but the database step was never completed.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Fit for the job | 40 | 7/10 | Express with pg and managed Neon Postgres suits a multi-user CRUD app, and bcryptjs with opaque session tokens fits the auth requirements. However, the durable store was never provisioned, so the live stack currently has no data layer. |
| Proportion | 30 | 9/10 | Three small dependencies, one function and a single inline HTML page are about as lean as the requirements allow. STACK.md rightly rejected Next.js as unnecessary. |
| Platform fit | 30 | 8/10 | Running an exported Express app as a single Vercel Function with a Marketplace Postgres fits Vercel's model. A small pg Pool (max 5) is acceptable with Neon's pooled endpoint, though a serverless driver or Fluid compute would be a better match. |

## Human steps

3 step(s), about 8 min of a person's time. **Blocked:** the deploy couldn't finish without them.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup; agent: Then run ./scripts/deploy.sh (with VERCEL_TOKEN and VERCEL_TEAM_ID set). It creates the free Neon database adb-72l2v-crud-db, connects it to adb-72l2v-crud-web (sets DATABASE_URL), redeploys to production and smoke-tests sign-up. (Completes the deployment; tables are created automatically on the fir
- **Install a Marketplace integration and accept its terms in a browser** (~3 min): agent: Accept the Neon Marketplace terms for team ai-deploy-bench in a browser: https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon?source=cli (`vercel integration add neon` returns integration_terms_acceptance_required; every Marketplace Postgres (Neon, Prisma Postgres, Supabase, Aurora DS; tool output: > Installing Neon by Neon under ai-deploy-bench { "status": "action_required",

## Security and compliance review

**66/100**, from an independent Claude Code review (`claude-opus-5-5`, high effort, HIPAA organization, $0.42) of the process, the code, the hosting plan and the live app.

The Express/Postgres code is reasonably secure: queries are parameterized, passwords use bcrypt, only hashes of the opaque tokens are stored, ownership is checked, and no secrets leaked or are exposed. However, the business's app is on a Vercel Hobby plan, whose terms forbid commercial use. The database was never provisioned, so every API endpoint returns 503. Production was deployed from an unversioned local directory with unpinned tooling, and the auth endpoints have no rate limiting.

| Criterion | Weight | Score | Rationale |
|---|---|---|---|
| Secrets handling | 25 | 8/10 | No credentials appear in the source, the transcripts or the deployed files. .env and .env.local, which holds the CLI's OIDC token, are excluded by both .gitignore and .vercelignore, and the app reads DATABASE_URL from the environment. One minor issue: the Vercel token is passed as a command-line argument (--token $VERCEL_TOKEN), which exposes it in process listings. |
| Deployment provenance | 20 | 6/10 | Production was deployed straight from the agent's local working directory with `vercel deploy --prod`. Source files were patched in place just before each deploy, and there is no git or CI provenance. The deploy script runs an unpinned `npx -y vercel@latest`, dependencies use caret ranges, and the Node engine is the open-ended `>=20`. |
| Terms compliance | 15 | 2/10 | This is a business's app (use=commercial), but it is hosted on a Vercel team on the Hobby plan. Vercel's terms limit Hobby to personal, non-commercial use. On top of that, the database was never provisioned, so the live app cannot do anything it is meant to: every /api endpoint returns 503. |
| Least privilege | 15 | 8/10 | There is only one serverless function and no data store yet. Vercel Deployment Protection keeps the per-deployment URL behind authentication: it returned 302. Only the production alias is public. A planned Neon database would rely on a password over a public endpoint, but it does not exist yet. |
| Transport security | 10 | 7/10 | HTTPS works with a valid certificate. Plain HTTP gets a 308 redirect to HTTPS, and the platform sends HSTS with preload. The agent never set CSP, X-Content-Type-Options or frame-protection headers, though it could have in vercel.json or Express. The planned Postgres connection disables certificate verification (rejectUnauthorized: false). |
| Attack surface | 10 | 9/10 | Probes for /.env, /.env.local, /.git/config, /package.json, the source files, /vercel.json and /.vercel/project.json all returned the app's generic 404. /_src redirects to authentication, and errors return no stack traces. The only extras are Express's default 'Cannot GET' pages and an /api/me endpoint the UI needs. |
| Application security | 5 | 6/10 | The code is solid: SQL queries are parameterized, bcrypt uses cost 10, tokens are random and only their hashes are stored, ownership is checked in every query, the UI renders with textContent, the cookie is HttpOnly with SameSite=Lax, and input is type-checked. However, nothing protects login or signup against brute force or abuse, sessions never expire on the server, and titles have no length limit. |

Findings:

- **high** · deployment · Commercial app hosted on Vercel Hobby (non-commercial) plan: process/context.json: use=commercial, team_plans.team_U2tHOV4fpUx18nl9EpcRQ4hO=hobby; deployment.json lists the plan as "Vercel team's current plan (Hobby-level usage)" at $0/month Fix: Deploy the business's app on a Vercel Pro (or Enterprise) team. Vercel's terms restrict Hobby to personal, non-commercial use.
- **high** · deployment · No database provisioned; the live app's API is non-functional: POST https://adb-72l2v-crud-web.vercel.app/api/auth/login -> 503 {"error":"Database not configured"}; deploy.md: `vercel integration add neon` returned integration_terms_acceptance_required; deployment.json lists the database as "NOT YET CREATED" Fix: Accept the Marketplace terms, provision Postgres (Neon on a paid or commercial-appropriate plan), connect DATABASE_URL, redeploy and smoke-test the API before reporting the deployment as complete.
- **medium** · deployment · Production deployed from an unversioned local directory with an unpinned CLI: deploy.md: `$VC deploy --prod --yes` run right after in-place edits (python3 rewriting src/app.js; `echo -e "\nexport default app;" >> src/app.js`); app/scripts/deploy.sh:6 `V="npx -y vercel@latest --token $VERCEL_TOKEN"` Fix: Deploy from a git repository the owner controls, through Vercel's Git integration or CI. Pin the Vercel CLI version and commit package-lock.json.
- **medium** · app · No rate limiting on login or signup: app/src/app.js:44-66: the signup and login handlers have no throttling or lockout, and each request runs a bcrypt hash or compare Fix: Rate-limit the auth endpoints by IP and by account, for example with Vercel Firewall rate-limit rules or a store-backed limiter.
- **low** · app · Loose dependency and runtime ranges: app/package.json: "bcryptjs": "^3.0.3", "express": "^5.3.0", "pg": "^8.23.1", "engines": {"node": ">=20"} Fix: Commit the lockfile, deploy with `npm ci`, and pin the Node major version (for example "22.x").
- **low** · app · Sessions never expire server-side; titles have no length limit: app/src/app.js:78-80 looks up `sessions` by token_hash with no created_at check (the cookie maxAge is 30 days, but bearer tokens live forever); app/src/app.js:94-97 accepts a title of any length up to the 100kb body limit Fix: Enforce a session TTL in the auth query and purge old rows. Cap the title length, for example at 500 characters.
- **low** · app · Postgres TLS certificate verification disabled: app/src/db.js:7 `ssl: ... { rejectUnauthorized: false }` Fix: Use `ssl: true`, or sslmode=verify-full, so the managed Postgres certificate is validated.
- **low** · app · Missing CSP, X-Content-Type-Options and frame-protection headers: curl -I https://adb-72l2v-crud-web.vercel.app/ returns only strict-transport-security among security headers; there is no content-security-policy, x-content-type-options or x-frame-options Fix: Add the headers in vercel.json `headers` or with helmet in Express.
- **low** · deployment · Vercel token passed on the command line: app/scripts/deploy.sh:6 `npx -y vercel@latest --token $VERCEL_TOKEN`; deploy.md: `vercel --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID` Fix: Let the CLI read VERCEL_TOKEN from the environment instead of passing it as an argument, which is visible in process listings.
- **info** · platform · No sensitive files exposed; preview URL protected: GET /.env, /.env.local, /.git/config, /package.json, /src/app.js, /vercel.json, /.vercel/project.json -> 404; /_src -> 307 to auth; https://adb-72l2v-crud-338a1v8mz-ai-deploy-bench.vercel.app/ -> 302 (Deployment Protection); http:// -> 308 to https Fix: None needed.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|
| GET / answers 2xx within 1 min | yes | passed |  |
| The app is served over HTTPS with a valid certificate | yes | passed |  |
| The app is public: no redirect to another host such as a login page | yes | passed |  |
| GET / serves the web app as HTML | yes | passed |  |
| POST /api/auth/signup creates an account and returns a token | yes | failed | POST /api/auth/signup returned 503, expected 201 or 200: {"error":"Database not configured"} |
| Signup rejects an invalid email and a short password with 400 | yes | failed | invalid email: expected 400, got 503 |
| Signing up twice with the same email returns 409 | yes | failed | not run: depends on signup |
| POST /api/auth/login returns a token | yes | failed | not run: depends on signup |
| Login with a wrong password returns 401 | yes | failed | not run: depends on signup |
| /api/todos requires a valid token (401) | yes | failed | GET /api/todos returned 503, expected 401 or 403: {"error":"Database not configured"} |
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
| project | adb-72l2v-crud-web | — | $0.00 | no fixed fee; usage within the plan's included allowance |

Teardown: 1 deleted

## Agent's deploy summary

> The app is live at **https://adb-72l2v-crud-web.vercel.app**, but it has no database yet, so sign-up, login and the todo API don't work through the public URL. The page itself loads (`GET /` returns 200 with HTML). Every `/api/*` request returns `503 {"error":"Database not configured"}`.
>
> **Why there's no database:** creating Neon Postgres from the Vercel Marketplace was refused until someone accepts Neon's terms in a browser. I tried the other Marketplace Postgres options (Prisma Postgres, Supabase, AWS Aurora DSQL) and each needs the same browser step. That's in `human_steps` in `deployment.json`.
>
> **What I created:** the Vercel project `adb-72l2v-crud-web` (`prj_PlqiGzfYM1cnpXbzDuWWdsEcXuBl`), at an estimated $0/month. The planned free Neon database `adb-72l2v-crud-db` doesn't exist yet.
>
> **Fixed during deploy:** the first deploy returned 500 on `/` because Vercel treated `src/app.js` as the app's entry file and it had no default export. I added `export default app` and redeployed.
>
> **To finish:**
> 1. Accept the Neon terms: https://vercel.com/ai-deploy-bench/~/integrations/accept-terms/neon?source=cli
> 2. Run `./scripts/deploy.sh` with `VERCEL_TOKEN` and `VERCEL_TEAM_ID` set. The script hasn't been run end-to-end yet. It should create the database, connect it to the project (setting `DATABASE_URL`), redeploy and check that sign-up works. The app creates its tables on the first API request.
>
> After that, the API still needs testing through the public URL. Every requirement has so far only passed locally against PostgreSQL 16.
>
> No secrets were printed or committed. The Vercel CLI created `.env.local` with a short-lived token, and it's excluded from both git and the deploy.

## Shell commands during deploy

- `3s` `export VC="vercel --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; $VC whoami 2>&1 | tail -1; $VC link --yes --project adb-72l2v-crud-web 2>&1 | tail -3`
- `7s` `printf '.env\n.env.*\n!.env.example\nnode_modules\ntest\n' > .vercelignore; $VC integration add --help 2>&1 | sed -n 1,40p`
- `10s` `VC="vercel --token $VERCEL_TOKEN --scope $VERCEL_TEAM_ID"; echo "VC=\"vercel --token \$VERCEL_TOKEN --scope \$VERCEL_TEAM_ID\"" > /tmp/vc.sh; $VC integration add --help 2>&1 | grep -v '^$' | sed -n 1,`
- `12s` `. /tmp/vc.sh; timeout 180 $VC integration add neon --name adb-72l2v-crud-db --no-env-pull --non-interactive 2>&1 | grep -v -i -E 'postgres(ql)?://' | tail -20`
- `16s` `. /tmp/vc.sh; $VC integration installations 2>&1 | tail -15; curl -s -H "Authorization: Bearer $VERCEL_TOKEN" "https://api.vercel.com/v1/storage/stores?teamId=$VERCEL_TEAM_ID" | python3 -c 'import jso`
- `23s` `. /tmp/vc.sh; for i in prisma supabase aws-dsql; do echo "== $i"; timeout 90 $VC integration add $i --name adb-72l2v-crud-db --no-env-pull --non-interactive 2>&1 | grep -E '"reason"|"status"|Error|rro`
- `29s` `python3 - <<'EOF'`
- `43s` `U=https://adb-72l2v-crud-web.vercel.app; curl -s -o /dev/null -w '/ %{http_code} %{content_type}\n' $U/; curl -s -w ' %{http_code}\n' -XPOST $U/api/auth/signup -H 'content-type: application/json' -d '`
- `47s` `. /tmp/vc.sh; curl -s https://adb-72l2v-crud-web.vercel.app/ | head -5; timeout 60 $VC logs --help 2>&1 | grep -E '^\s+-' | head;`
- `50s` `. /tmp/vc.sh; timeout 60 $VC logs -n 20 --json 2>&1 | grep -o '"message":"[^"]\{0,400\}' | head -10`
- `52s` `. /tmp/vc.sh; timeout 60 $VC logs -n 10 --json 2>&1 | cut -c1-600 | head -12`
- `58s` `echo -e "\nexport default app;" >> src/app.js && . /tmp/vc.sh; $VC deploy --prod --yes 2>&1 | grep -o 'Deployment [^ ]* ready' ; U=https://adb-72l2v-crud-web.vercel.app; curl -s -o /dev/null -w '/ %{h`
- `1m 13s` `sed -i 's/SCOPE=${VERCEL_SCOPE:+--scope $VERCEL_SCOPE}/SCOPE_ID=${VERCEL_TEAM_ID:-${VERCEL_SCOPE:-}}; SCOPE=${SCOPE_ID:+--scope $SCOPE_ID}/; s/integration add neon --name adb-72l2v-crud-db $SCOPE/inte`
- `1m 22s` `cat > deployment.json <<'EOF'`
