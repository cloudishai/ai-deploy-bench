# Benchmark run 2026-10-15_14-1

- Date: 2026-10-15
- Benchmark version: 3 ([changes](../../../CHANGES.md))
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: full
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38673129065
- Reran clouds: railway; the other cells are copied unchanged from [2026-10-14 · #13](../2026-10-14_13-1/summary.md)

## Summary

| Cloud | Success | Deploys without human | Human steps | Human time | Security & compliance | Stack fit | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 5/5 | 5/5 | 0 | 0 min | 80/100 | 89/100 | 100% | 2m 35s | 3m 30s | 7.09M | $4.61 | $0.55 | $39.20 |
| [DigitalOcean](https://www.digitalocean.com) | 5/5 | 0/5 | 3 | 7 min | 84/100 | 84/100 | 100% | 2m 33s | 4m 23s | 6.40M | $4.61 | $39.00 | $39.00 |
| [Render](https://render.com) | 5/5 | 0/5 | 2 | 5 min | 70/100 | 80/100 | 100% | 2m 17s | 3m 27s | 7.50M | $5.64 | $0.00 | $35.65 |
| [Vercel](https://vercel.com) | 4/5 | 0/5 | 3 | 8 min | 78/100 | 75/100 | 85% | 2m 19s | 9m 29s | 20.04M | $10.21 | $60.00 | $100.00 |
| [Railway](https://railway.com) | 0/5 | 0/5 | 3 | 7 min | — | — | 0% | 2m 01s | 1m 46s | 6.48M | $4.16 | $0.00 | $0.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site | CRUD app | API | Dashboard | Realtime chat |
|---|---|---|---|---|---|
| Cloudish | ✅ | ✅ | ✅ | ✅ | ✅ |
| DigitalOcean | ✅ | ✅ | ✅ | ✅ | ✅ |
| Render | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vercel | ✅ | 🙋 needs a person | ✅ | ✅ | ✅ |
| Railway | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Stack fit | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) (from 2026-10-14 · #13) | 16/16 | 0 | 0 min | 81/100 | 90/100 | 1m 43s | 2m 35s | 0s | 897.4K | $0.65 | $0.11 | $7.84 |
| opus-5-5 | cloudish | crud | 1 | [✅ success](cells/opus-5-5/cloudish/crud-t1.md) (from 2026-10-14 · #13) | 19/19 | 0 | 0 min | 76/100 | 86/100 | 2m 31s | 2m 58s | 0s | 1.35M | $0.91 | $0.11 | $7.84 |
| opus-5-5 | cloudish | api | 1 | [✅ success](cells/opus-5-5/cloudish/api-t1.md) (from 2026-10-14 · #13) | 20/20 | 0 | 0 min | 76/100 | 87/100 | 2m 30s | 5m 10s | 0s | 1.23M | $0.86 | $0.11 | $7.84 |
| opus-5-5 | cloudish | dataviz | 1 | [✅ success](cells/opus-5-5/cloudish/dataviz-t1.md) (from 2026-10-14 · #13) | 12/12 | 0 | 0 min | 80/100 | 93/100 | 3m 28s | 2m 43s | 0s | 2.20M | $1.26 | $0.11 | $7.84 |
| opus-5-5 | cloudish | realtime | 1 | [✅ success](cells/opus-5-5/cloudish/realtime-t1.md) (from 2026-10-14 · #13) | 13/13 | 0 | 0 min | 86/100 | 90/100 | 2m 43s | 4m 04s | 0s | 1.41M | $0.92 | $0.11 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) (from 2026-10-14 · #13) | 16/16 | 3 | 7 min | 91/100 | 81/100 | 2m 02s | 2m 07s | 0s | 1.10M | $0.75 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | crud | 1 | [✅ success](cells/opus-5-5/digitalocean/crud-t1.md) (from 2026-10-14 · #13) | 19/19 | 3 | 7 min | 78/100 | 83/100 | 2m 39s | 7m 18s | 0s | 1.25M | $0.93 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | api | 1 | [✅ success](cells/opus-5-5/digitalocean/api-t1.md) (from 2026-10-14 · #13) | 20/20 | 3 | 7 min | 82/100 | 87/100 | 2m 59s | 8m 55s | 0s | 1.51M | $1.21 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | dataviz | 1 | [✅ success](cells/opus-5-5/digitalocean/dataviz-t1.md) (from 2026-10-14 · #13) | 12/12 | 3 | 7 min | 81/100 | 87/100 | 2m 53s | 1m 49s | 0s | 1.49M | $0.96 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | realtime | 1 | [✅ success](cells/opus-5-5/digitalocean/realtime-t1.md) (from 2026-10-14 · #13) | 13/13 | 3 | 7 min | 89/100 | 82/100 | 2m 10s | 1m 45s | 0s | 1.05M | $0.77 | $5.00 | $5.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) (from 2026-10-14 · #13) | 16/16 | 2 | 5 min | 72/100 | 81/100 | 1m 34s | 1m 49s | 0s | 1.33M | $1.00 | $0.00 | $7.13 |
| opus-5-5 | render | crud | 1 | [✅ success](cells/opus-5-5/render/crud-t1.md) (from 2026-10-14 · #13) | 19/19 | 2 | 5 min | 62/100 | 84/100 | 2m 26s | 4m 05s | 0s | 1.29M | $1.01 | $0.00 | $7.13 |
| opus-5-5 | render | api | 1 | [✅ success](cells/opus-5-5/render/api-t1.md) (from 2026-10-14 · #13) | 20/20 | 2 | 5 min | 71/100 | 80/100 | 2m 34s | 3m 58s | 0s | 1.63M | $1.26 | $0.00 | $7.13 |
| opus-5-5 | render | dataviz | 1 | [✅ success](cells/opus-5-5/render/dataviz-t1.md) (from 2026-10-14 · #13) | 12/12 | 2 | 5 min | 75/100 | 81/100 | 2m 24s | 2m 30s | 0s | 1.66M | $1.15 | $0.00 | $7.13 |
| opus-5-5 | render | realtime | 1 | [✅ success](cells/opus-5-5/render/realtime-t1.md) (from 2026-10-14 · #13) | 13/13 | 2 | 5 min | 70/100 | 74/100 | 2m 28s | 4m 54s | 0s | 1.59M | $1.23 | $0.00 | $7.13 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) (from 2026-10-14 · #13) | 16/16 | 2 | 5 min | 73/100 | 100/100 | 1m 40s | 1m 14s | 0s | 1.84M | $1.00 | $20.00 | $20.00 |
| opus-5-5 | vercel | crud | 1 | [⚠️ partial](cells/opus-5-5/vercel/crud-t1.md) (from 2026-10-14 · #13) | 5/19 | 3 | 8 min | 69/100 | 83/100 | 2m 03s | 1m 41s | 0s | 1.73M | $1.07 | $20.00 | $20.00 |
| opus-5-5 | vercel | api | 1 | [✅ success](cells/opus-5-5/vercel/api-t1.md) (from 2026-10-14 · #13) | 20/20 | 2 | 5 min | 85/100 | 46/100 | 2m 19s | 18m 35s | 0s | 5.38M | $2.79 | $0.00 | $20.00 |
| opus-5-5 | vercel | dataviz | 1 | [✅ success](cells/opus-5-5/vercel/dataviz-t1.md) (from 2026-10-14 · #13) | 12/12 | 2 | 5 min | 77/100 | 93/100 | 2m 21s | 1m 10s | 0s | 3.04M | $1.54 | $20.00 | $20.00 |
| opus-5-5 | vercel | realtime | 1 | [✅ success](cells/opus-5-5/vercel/realtime-t1.md) (from 2026-10-14 · #13) | 13/13 | 2 | 5 min | 88/100 | 53/100 | 3m 14s | 24m 45s | 0s | 8.05M | $3.81 | $0.00 | $20.00 |
| opus-5-5 | railway | static | 1 | [❌ failed](cells/opus-5-5/railway/static-t1.md) | 0/0 | 3 | 7 min | — | — | 1m 40s | 1m 33s | — | 1.35M | $0.88 | $0.00 | $0.00 |
| opus-5-5 | railway | crud | 1 | [❌ failed](cells/opus-5-5/railway/crud-t1.md) | 0/0 | 3 | 7 min | — | — | 1m 54s | 1m 04s | — | 1.03M | $0.70 | $0.00 | $0.00 |
| opus-5-5 | railway | api | 1 | [❌ failed](cells/opus-5-5/railway/api-t1.md) | 0/0 | 3 | 7 min | — | — | 2m 19s | 1m 58s | — | 1.40M | $0.92 | $0.00 | $0.00 |
| opus-5-5 | railway | dataviz | 1 | [❌ failed](cells/opus-5-5/railway/dataviz-t1.md) | 0/0 | 3 | 7 min | — | — | 2m 30s | 3m 10s | — | 1.74M | $0.99 | $0.00 | $0.00 |
| opus-5-5 | railway | realtime | 1 | [❌ failed](cells/opus-5-5/railway/realtime-t1.md) | 0/0 | 3 | 7 min | — | — | 1m 42s | 1m 03s | — | 964.9K | $0.67 | $0.00 | $0.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | Node.js 22, Node.js http | 443 | 0 | Dockerfile, .dockerignore | 307.2K | 590.2K |
| opus-5-5 | cloudish | crud | 1 | Node.js 24, Node.js http, SQLite | 487 | 0 | Dockerfile, .dockerignore | 429.7K | 921.7K |
| opus-5-5 | cloudish | api | 1 | Python 3.12, FastAPI, SQLite | 324 | 4 | Dockerfile, .dockerignore | 447.9K | 786.4K |
| opus-5-5 | cloudish | dataviz | 1 | Node.js 22, Node.js http | 471 | 0 | Dockerfile, .dockerignore | 885.7K | 1.31M |
| opus-5-5 | cloudish | realtime | 1 | Node.js 24, Node.js http, SQLite | 474 | 1 | Dockerfile, .dockerignore | 599.5K | 812.5K |
| opus-5-5 | digitalocean | static | 1 | Node.js 22, Node.js http | 458 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 459.9K | 363.7K |
| opus-5-5 | digitalocean | crud | 1 | Node.js 24, Express, PostgreSQL | 512 | 4 | Dockerfile, docker-compose.yml, .dockerignore, .do/app.yaml | 488.3K | 419.5K |
| opus-5-5 | digitalocean | api | 1 | Python 3.12, FastAPI, PostgreSQL | 449 | 6 | Dockerfile, .dockerignore, .do/app.yaml | 449.7K | 677.4K |
| opus-5-5 | digitalocean | dataviz | 1 | Node.js 20, Express | 501 | 2 | Dockerfile, .dockerignore, .do/app.yaml | 692.2K | 448.4K |
| opus-5-5 | digitalocean | realtime | 1 | Node.js 22, Node.js http | 563 | 1 | Dockerfile, .dockerignore, .do/app.yaml | 432.4K | 325.4K |
| opus-5-5 | render | static | 1 | Node.js 22, Node.js http | 515 | 0 | render.yaml | 377.0K | 666.4K |
| opus-5-5 | render | crud | 1 | Node.js 20+, Express, PostgreSQL | 507 | 3 | render.yaml | 367.3K | 610.8K |
| opus-5-5 | render | api | 1 | Node.js 20+, Express, PostgreSQL | 689 | 2 | render.yaml | 496.1K | 741.8K |
| opus-5-5 | render | dataviz | 1 | Node.js 22, Node.js http | 636 | 0 | render.yaml | 607.8K | 755.8K |
| opus-5-5 | render | realtime | 1 | Node.js 22, Node.js http, PostgreSQL | 746 | 2 | render.yaml | 446.0K | 813.4K |
| opus-5-5 | vercel | static | 1 | Node.js 18+, Vercel Functions | 369 | 0 | vercel.json | 420.0K | 453.1K |
| opus-5-5 | vercel | crud | 1 | Node.js, Express | 406 | 3 | vercel.json | 320.8K | 640.4K |
| opus-5-5 | vercel | api | 1 | Node.js, Hono | 862 | 6 | — | 414.5K | 4.26M |
| opus-5-5 | vercel | dataviz | 1 | Node.js 24, Vercel Functions | 524 | 0 | vercel.json | 575.3K | 768.7K |
| opus-5-5 | vercel | realtime | 1 | Node.js 20+, Next.js, React | 816 | 10 | — | 511.9K | 6.66M |
| opus-5-5 | railway | static | 1 | Node.js 20+, Node.js http | 399 | 0 | railway.json | 455.5K | 666.4K |
| opus-5-5 | railway | crud | 1 | Node.js 20+, Express | 367 | 3 | railway.json | 387.0K | 409.0K |
| opus-5-5 | railway | api | 1 | Node.js 20+, Express | 476 | 2 | railway.json | 410.1K | 689.1K |
| opus-5-5 | railway | dataviz | 1 | Node.js 20+, Node.js http | 449 | 0 | railway.json | 653.5K | 695.1K |
| opus-5-5 | railway | realtime | 1 | Node.js 20+, Node.js http | 384 | 1 | railway.json | 342.3K | 443.7K |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security & compliance* is an independent Claude Code review of how each app was deployed, whether its hosting plan fits how the app is used, and what is live, scored against a fixed rubric. *Stack fit* is the same review's rating of the stack the agent chose, judged against the app's requirements. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, are priced on the cheapest plan that allows it. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md#hosting-cost).

## Screenshots

What the verifier saw on each deployment. Each picture links to its cell's report, which has the rest.

| App | Cloudish | DigitalOcean | Render | Vercel |
|---|---|---|---|---|
| Static site | [<img src="cells/opus-5-5/cloudish/static-t1/home.jpg" width="220" alt="Static site on Cloudish">](cells/opus-5-5/cloudish/static-t1.md) | [<img src="cells/opus-5-5/digitalocean/static-t1/home.jpg" width="220" alt="Static site on DigitalOcean">](cells/opus-5-5/digitalocean/static-t1.md) | [<img src="cells/opus-5-5/render/static-t1/home.jpg" width="220" alt="Static site on Render">](cells/opus-5-5/render/static-t1.md) | [<img src="cells/opus-5-5/vercel/static-t1/home.jpg" width="220" alt="Static site on Vercel">](cells/opus-5-5/vercel/static-t1.md) |
| CRUD app | [<img src="cells/opus-5-5/cloudish/crud-t1/signin.jpg" width="220" alt="CRUD app on Cloudish">](cells/opus-5-5/cloudish/crud-t1.md) | [<img src="cells/opus-5-5/digitalocean/crud-t1/signin.jpg" width="220" alt="CRUD app on DigitalOcean">](cells/opus-5-5/digitalocean/crud-t1.md) | [<img src="cells/opus-5-5/render/crud-t1/signin.jpg" width="220" alt="CRUD app on Render">](cells/opus-5-5/render/crud-t1.md) | [<img src="cells/opus-5-5/vercel/crud-t1/signin.jpg" width="220" alt="CRUD app on Vercel">](cells/opus-5-5/vercel/crud-t1.md) |
| API | [<img src="cells/opus-5-5/cloudish/api-t1/docs.jpg" width="220" alt="API on Cloudish">](cells/opus-5-5/cloudish/api-t1.md) | [<img src="cells/opus-5-5/digitalocean/api-t1/docs.jpg" width="220" alt="API on DigitalOcean">](cells/opus-5-5/digitalocean/api-t1.md) | [<img src="cells/opus-5-5/render/api-t1/docs.jpg" width="220" alt="API on Render">](cells/opus-5-5/render/api-t1.md) | [<img src="cells/opus-5-5/vercel/api-t1/docs.jpg" width="220" alt="API on Vercel">](cells/opus-5-5/vercel/api-t1.md) |
| Dashboard | [<img src="cells/opus-5-5/cloudish/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Cloudish">](cells/opus-5-5/cloudish/dataviz-t1.md) | [<img src="cells/opus-5-5/digitalocean/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on DigitalOcean">](cells/opus-5-5/digitalocean/dataviz-t1.md) | [<img src="cells/opus-5-5/render/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Render">](cells/opus-5-5/render/dataviz-t1.md) | [<img src="cells/opus-5-5/vercel/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Vercel">](cells/opus-5-5/vercel/dataviz-t1.md) |
| Realtime chat | [<img src="cells/opus-5-5/cloudish/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Cloudish">](cells/opus-5-5/cloudish/realtime-t1.md) | [<img src="cells/opus-5-5/digitalocean/realtime-t1/chat.jpg" width="220" alt="Realtime chat on DigitalOcean">](cells/opus-5-5/digitalocean/realtime-t1.md) | [<img src="cells/opus-5-5/render/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Render">](cells/opus-5-5/render/realtime-t1.md) | [<img src="cells/opus-5-5/vercel/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Vercel">](cells/opus-5-5/vercel/realtime-t1.md) |
