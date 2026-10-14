# Benchmark run 2026-10-14_12-1

- Date: 2026-10-14
- Benchmark version: 3 ([changes](../../../CHANGES.md))
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: apps: static · clouds: railway · models: all
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38651736144

## Summary

| Cloud | Success | Deploys without human | Human steps | Human time | Security & compliance | Stack fit | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [Railway](https://railway.com) | 1/1 | 0/1 | 2 | 5 min | 85/100 | 90/100 | 100% | 2m 01s | 2m 35s | 1.14M | $0.81 | $0.00 | $0.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site |
|---|---|
| Railway | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Stack fit | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | railway | static | 1 | [✅ success](cells/opus-5-5/railway/static-t1.md) | 16/16 | 2 | 5 min | 85/100 | 90/100 | 2m 01s | 2m 35s | 0s | 1.14M | $0.81 | $0.00 | $0.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | railway | static | 1 | Node.js 18+, Node.js http | 457 | 0 | railway.json | 505.6K | 403.6K |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security & compliance* is an independent Claude Code review of how each app was deployed, whether its hosting plan fits how the app is used, and what is live, scored against a fixed rubric. *Stack fit* is the same review's rating of the stack the agent chose, judged against the app's requirements. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, are priced on the cheapest plan that allows it. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md#hosting-cost).

## Screenshots

What the verifier saw on each deployment. Each picture links to its cell's report, which has the rest.

| App | Railway |
|---|---|
| Static site | [<img src="cells/opus-5-5/railway/static-t1/home.jpg" width="220" alt="Static site on Railway">](cells/opus-5-5/railway/static-t1.md) |
