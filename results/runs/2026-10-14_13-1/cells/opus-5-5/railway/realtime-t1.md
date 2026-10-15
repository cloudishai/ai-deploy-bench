# ❌ Real-Time Collaborative App on Railway with Opus 5.5 (trial 1)

**failed** (failed at human): 0/0 checks passed (0%).

- URL: none
- Estimated hosting: Light use: $0.00/month, Busy: $0.00/month (the agent estimated $5.00)
- Agent: Claude Code 2.1.296, model `claude-opus-5-5`, effort medium, HIPAA organization
- Resource prefix: `adb-jhvas-realtime`

| | Build | Deploy | Total |
|---|---|---|---|
| Status | completed | completed | |
| Time | 1m 40s | 1m 01s | 5m 14s |
| Turns | 11 | 10 | |
| Tokens | 427.0K | 517.1K | 1.22M |
| Agent cost | $0.39 | $0.22 | $0.74 |
| Shell commands | 10 | 9 | |

App answered — after the agent finished deploying.

**Needed a human:** the no-credentials attempt didn't produce a working public URL, so the cloud's credentials were provided and the agent redeployed (that attempt took 2m 34s, 274.6K tokens, $0.14).

## What was built

- Runtime: Node.js 20+
- Frameworks: Node.js http module (built in)
- Libraries: ws
- Packaging: railway.json
- Code: 361 lines in 11 files (JavaScript 238, HTML 112, JSON 48, Markdown 31, Shell 11)
- Dependencies: 1 npm, 0 Python
- Deploy config: `railway.json`

### Stack fit

Not rated: no reachable deployment to review.

## Human steps

3 step(s), about 7 min of a person's time. **Blocked:** the deploy couldn't finish without them.

- **Sign up for an account and verify the email address** (~3 min): prerequisite: account setup
- **Create an API token and hand it to the agent** (~2 min): prerequisite: account setup
- **Add a payment method to the account** (~2 min): agent: In the Railway workspace "Javier Luraschi's Projects", either activate the plan (add a payment method / leave the free trial) or delete unneeded existing projects (adb-ytghj-static, adb-bbchf-static, which belong to other runs) to free provisioning capacity. Then run ./deploy.sh with RAILWAY_API_TOK

## Security and compliance review

Not scored: no reachable deployment to review.

## Checks

| Check | Required | Result | Detail |
|---|---|---|---|

Verification error: no deployment URL found

## Cloud resources

| Traffic | $/month | How it was priced |
|---|---|---|
| Light use | $0.00 | nothing deployed |
| Busy | $0.00 | nothing deployed |

Each resource's list price, at the size it was provisioned and always on:

None found.

Teardown: 0 deleted

## Agent's deploy summary

> I couldn't deploy the app: Railway refused to create the project, so there is no public URL yet and nothing has been tested through one.
>
> **What happened:** the token works (`railway whoami` shows Javier Luraschi's account). But creating project `adb-jhvas-realtime` failed with "Free plan resource provision limit exceeded. Please upgrade to provision more resources!" I got the same error from both `railway init` and Railway's API directly. No Railway resources were created.
>
> **Why:** the workspace is on a trial with $5 of credit and an inactive plan. It already holds two projects from other runs, `adb-ytghj-static` and `adb-bbchf-static`. I didn't change the plan, since the rules forbid it. I also didn't delete those projects or put my service inside them, because they aren't mine.
>
> **Human step (blocking, recorded in `deployment.json`):** do one of these in the Railway workspace:
> - Activate the plan, for example by adding a payment method.
> - Or delete the unused `adb-ytghj-static` and `adb-bbchf-static` projects to free up the limit.
>
> Then run `./deploy.sh` with `RAILWAY_API_TOKEN` set. It creates the project and the `adb-jhvas-realtime-web` service, uploads the code, and creates a public HTTPS domain. After that, fill in `url` as `https://<domain>` and `realtime.url` as `wss://<domain>/ws`.
>
> **`deployment.json`:** written, with an empty `url`. `realtime.transport` is `"websocket"`. The estimated cost is about $5/month on the Hobby plan, or $0 while trial credits last.
>
> The CLI also warned that `railway.json` (the deploy config) is deprecated. It still works until 2026-12-01.

## Shell commands during deploy

- `4s` `test -n "$RAILWAY_API_TOKEN" && echo token-set; which railway || npm i -g @railway/cli >/dev/null 2>&1; timeout 30 railway whoami 2>&1 </dev/null; timeout 30 railway list 2>&1 </dev/null | head`
- `8s` `timeout 60 railway init --name adb-jhvas-realtime --json </dev/null 2>&1 | tail -5 && timeout 60 railway add --service adb-jhvas-realtime-web --json </dev/null 2>&1 | tail -5`
- `14s` `cd /tmp && timeout 60 railway list --json </dev/null 2>/dev/null | python3 -c '`
- `21s` `curl -s https://backboard.railway.com/graphql/v2 -H "Authorization: Bearer $RAILWAY_API_TOKEN" -H 'content-type: application/json' -d '{"query":"{ me { workspaces { id name plan subscriptionModel cust`
- `24s` `curl -s https://backboard.railway.com/graphql/v2 -H "Authorization: Bearer $RAILWAY_API_TOKEN" -H 'content-type: application/json' -d '{"query":"mutation { projectCreate(input:{name:\"adb-jhvas-realti`
- `28s` `curl -s https://backboard.railway.com/graphql/v2 -H "Authorization: Bearer $RAILWAY_API_TOKEN" -H 'content-type: application/json' -d '{"query":"{ projects { edges { node { id name services { edges { `
- `32s` ❌ `sleep 35; curl -s https://backboard.railway.com/graphql/v2 -H "Authorization: Bearer $RAILWAY_API_TOKEN" -H 'content-type: application/json' -d '{"query":"mutation { projectCreate(input:{name:\"adb-jh`
- `35s` `until r=$(curl -s https://backboard.railway.com/graphql/v2 -H "Authorization: Bearer $RAILWAY_API_TOKEN" -H 'content-type: application/json' -d '{"query":"mutation { projectCreate(input:{name:\"adb-jh`
- `54s` `cat > deployment.json <<'EOF'`
