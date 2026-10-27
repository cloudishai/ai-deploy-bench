# Benchmark run 2026-10-27_17-1

- Date: 2026-10-27
- Benchmark version: 3 ([changes](../../../CHANGES.md))
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: full
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/40424719327
- Reran clouds: cloudish, railway, vercel; the other cells are copied unchanged from [2026-10-26 · #16](../2026-10-26_16-1/summary.md)

## Summary

| Cloud | Success | Deploys without human | Human steps | Human time | Security & compliance | Stack fit | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 5/5 | 5/5 | 0 | 0 min | 81/100 | 91/100 | 100% | 2m 07s | 2m 43s | 6.49M | $4.55 | $0.55 | $39.20 |
| [DigitalOcean](https://www.digitalocean.com) | 5/5 | 0/5 | 3 | 7 min | 84/100 | 85/100 | 100% | 2m 03s | 4m 30s | 5.64M | $4.52 | $39.00 | $39.00 |
| [Railway](https://railway.com) | 5/5 | 0/5 | 3 | 7 min | 79/100 | 88/100 | 100% | 1m 56s | 3m 40s | 7.71M | $4.65 | $36.99 | $188.19 |
| [Render](https://render.com) | 5/5 | 0/5 | 2 | 5 min | 70/100 | 80/100 | 100% | 2m 03s | 3m 52s | 7.00M | $4.97 | $0.00 | $35.65 |
| [Vercel](https://vercel.com) | 3/5 | 0/5 | 3 | 8 min | 76/100 | 77/100 | 81% | 2m 15s | 4m 57s | 16.25M | $8.18 | $60.00 | $100.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site | CRUD app | API | Dashboard | Realtime chat |
|---|---|---|---|---|---|
| Cloudish | ✅ | ✅ | ✅ | ✅ | ✅ |
| DigitalOcean | ✅ | ✅ | ✅ | ✅ | ✅ |
| Railway | ✅ | ✅ | ✅ | ✅ | ✅ |
| Render | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vercel | ✅ | 🙋 needs a person | ✅ | ✅ | 🙋 needs a person |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Stack fit | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | 0 | 0 min | 83/100 | 87/100 | 2m 05s | 1m 15s | 0s | 1.05M | $0.85 | $0.11 | $7.84 |
| opus-5-5 | cloudish | crud | 1 | [✅ success](cells/opus-5-5/cloudish/crud-t1.md) | 19/19 | 0 | 0 min | 78/100 | 93/100 | 2m 07s | 4m 45s | 0s | 1.45M | $0.97 | $0.11 | $7.84 |
| opus-5-5 | cloudish | api | 1 | [✅ success](cells/opus-5-5/cloudish/api-t1.md) | 20/20 | 0 | 0 min | 82/100 | 93/100 | 2m 23s | 4m 14s | 0s | 1.63M | $1.06 | $0.11 | $7.84 |
| opus-5-5 | cloudish | dataviz | 1 | [✅ success](cells/opus-5-5/cloudish/dataviz-t1.md) | 12/12 | 0 | 0 min | 84/100 | 93/100 | 2m 00s | 1m 41s | 0s | 1.39M | $0.91 | $0.11 | $7.84 |
| opus-5-5 | cloudish | realtime | 1 | [✅ success](cells/opus-5-5/cloudish/realtime-t1.md) | 13/13 | 0 | 0 min | 76/100 | 90/100 | 2m 00s | 1m 42s | 0s | 952.1K | $0.75 | $0.11 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) (from 2026-10-26 · #16) | 16/16 | 3 | 7 min | 87/100 | 84/100 | 1m 40s | 2m 10s | 0s | 1.09M | $0.84 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | crud | 1 | [✅ success](cells/opus-5-5/digitalocean/crud-t1.md) (from 2026-10-26 · #16) | 19/19 | 3 | 7 min | 79/100 | 87/100 | 2m 24s | 7m 19s | 0s | 1.16M | $1.05 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | api | 1 | [✅ success](cells/opus-5-5/digitalocean/api-t1.md) (from 2026-10-26 · #16) | 20/20 | 3 | 7 min | 81/100 | 87/100 | 2m 21s | 9m 00s | 0s | 1.15M | $1.01 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | dataviz | 1 | [✅ success](cells/opus-5-5/digitalocean/dataviz-t1.md) (from 2026-10-26 · #16) | 12/12 | 3 | 7 min | 89/100 | 90/100 | 2m 11s | 2m 08s | 0s | 1.39M | $0.93 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | realtime | 1 | [✅ success](cells/opus-5-5/digitalocean/realtime-t1.md) (from 2026-10-26 · #16) | 13/13 | 3 | 7 min | 84/100 | 79/100 | 1m 39s | 1m 51s | 0s | 847.9K | $0.69 | $5.00 | $5.00 |
| opus-5-5 | railway | static | 1 | [✅ success](cells/opus-5-5/railway/static-t1.md) | 16/16 | 3 | 7 min | 79/100 | 90/100 | 1m 24s | 3m 39s | 0s | 1.19M | $0.72 | $5.28 | $27.63 |
| opus-5-5 | railway | crud | 1 | [✅ success](cells/opus-5-5/railway/crud-t1.md) | 19/19 | 3 | 7 min | 76/100 | 90/100 | 2m 22s | 5m 27s | 0s | 2.09M | $1.17 | $10.57 | $52.65 |
| opus-5-5 | railway | api | 1 | [✅ success](cells/opus-5-5/railway/api-t1.md) | 20/20 | 3 | 7 min | 80/100 | 90/100 | 2m 10s | 4m 33s | 0s | 1.73M | $1.07 | $10.58 | $52.65 |
| opus-5-5 | railway | dataviz | 1 | [✅ success](cells/opus-5-5/railway/dataviz-t1.md) | 12/12 | 3 | 7 min | 78/100 | 90/100 | 2m 13s | 2m 26s | 0s | 1.62M | $0.96 | $5.28 | $27.63 |
| opus-5-5 | railway | realtime | 1 | [✅ success](cells/opus-5-5/railway/realtime-t1.md) | 13/13 | 3 | 7 min | 82/100 | 82/100 | 1m 31s | 2m 14s | 0s | 1.08M | $0.73 | $5.28 | $27.63 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) (from 2026-10-26 · #16) | 16/16 | 2 | 5 min | 72/100 | 81/100 | 1m 36s | 2m 22s | 0s | 1.07M | $0.80 | $0.00 | $7.13 |
| opus-5-5 | render | crud | 1 | [✅ success](cells/opus-5-5/render/crud-t1.md) (from 2026-10-26 · #16) | 19/19 | 2 | 5 min | 64/100 | 80/100 | 2m 12s | 4m 44s | 0s | 1.71M | $1.17 | $0.00 | $7.13 |
| opus-5-5 | render | api | 1 | [✅ success](cells/opus-5-5/render/api-t1.md) (from 2026-10-26 · #16) | 20/20 | 2 | 5 min | 68/100 | 81/100 | 2m 30s | 5m 57s | 0s | 1.61M | $1.13 | $0.00 | $7.13 |
| opus-5-5 | render | dataviz | 1 | [✅ success](cells/opus-5-5/render/dataviz-t1.md) (from 2026-10-26 · #16) | 12/12 | 2 | 5 min | 69/100 | 81/100 | 2m 15s | 4m 35s | 0s | 1.62M | $1.04 | $0.00 | $7.13 |
| opus-5-5 | render | realtime | 1 | [✅ success](cells/opus-5-5/render/realtime-t1.md) (from 2026-10-26 · #16) | 13/13 | 2 | 5 min | 78/100 | 76/100 | 1m 43s | 1m 41s | 0s | 986.1K | $0.83 | $0.00 | $7.13 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 | 5 min | 76/100 | 97/100 | 1m 43s | 45s | 0s | 1.72M | $1.05 | $20.00 | $20.00 |
| opus-5-5 | vercel | crud | 1 | [⚠️ partial](cells/opus-5-5/vercel/crud-t1.md) | 5/19 | 3 | 8 min | 66/100 | 79/100 | 2m 00s | 1m 29s | 0s | 1.92M | $1.06 | $20.00 | $20.00 |
| opus-5-5 | vercel | api | 1 | [✅ success](cells/opus-5-5/vercel/api-t1.md) | 20/20 | 2 | 5 min | 80/100 | 62/100 | 2m 23s | 17m 45s | 0s | 7.42M | $3.33 | $0.00 | $20.00 |
| opus-5-5 | vercel | dataviz | 1 | [✅ success](cells/opus-5-5/vercel/dataviz-t1.md) | 12/12 | 2 | 5 min | 75/100 | 90/100 | 2m 31s | 49s | 0s | 1.94M | $1.09 | $20.00 | $20.00 |
| opus-5-5 | vercel | realtime | 1 | [⚠️ partial](cells/opus-5-5/vercel/realtime-t1.md) | 10/13 | 3 | 8 min | 80/100 | 59/100 | 2m 39s | 3m 57s | 0s | 3.25M | $1.65 | $0.00 | $20.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | Node.js 24, Node.js http | 477 | 0 | Dockerfile, .dockerignore | 453.1K | 600.1K |
| opus-5-5 | cloudish | crud | 1 | Node.js 24, Node.js http, SQLite | 454 | 0 | Dockerfile, .dockerignore | 406.7K | 1.05M |
| opus-5-5 | cloudish | api | 1 | Node.js 24, Node.js http, SQLite | 577 | 0 | Dockerfile, .dockerignore | 467.7K | 1.17M |
| opus-5-5 | cloudish | dataviz | 1 | Node.js 24, Node.js http | 416 | 0 | Dockerfile, .dockerignore | 497.8K | 894.5K |
| opus-5-5 | cloudish | realtime | 1 | Node.js 22, Node.js http, SQLite | 475 | 1 | Dockerfile, .dockerignore | 370.1K | 582.0K |
| opus-5-5 | digitalocean | static | 1 | Node.js 22, Node.js http | 434 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 455.3K | 360.6K |
| opus-5-5 | digitalocean | crud | 1 | Node.js 22, Express, PostgreSQL | 472 | 3 | Dockerfile, .dockerignore, .do/app.yaml | 491.3K | 353.6K |
| opus-5-5 | digitalocean | api | 1 | Python 3.12, FastAPI, PostgreSQL | 358 | 6 | Dockerfile, .dockerignore | 438.4K | 401.5K |
| opus-5-5 | digitalocean | dataviz | 1 | Node.js 20, Node.js http | 540 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 645.9K | 448.4K |
| opus-5-5 | digitalocean | realtime | 1 | Node.js 20, Node.js http | 442 | 1 | Dockerfile, .dockerignore, .do/app.yaml | 343.9K | 264.1K |
| opus-5-5 | railway | static | 1 | Node.js 18+, Node.js http | 401 | 0 | railway.json | 339.0K | 589.8K |
| opus-5-5 | railway | crud | 1 | Node.js 20+, Express | 378 | 3 | railway.json | 572.6K | 1.12M |
| opus-5-5 | railway | api | 1 | Node.js 20+, Express | 443 | 2 | railway.json | 408.4K | 1.07M |
| opus-5-5 | railway | dataviz | 1 | Node.js 20+, Node.js http | 472 | 0 | railway.json | 596.1K | 743.6K |
| opus-5-5 | railway | realtime | 1 | Node.js 20+, Node.js http | 397 | 1 | railway.json | 341.3K | 508.0K |
| opus-5-5 | render | static | 1 | Node.js 24, Node.js http | 421 | 0 | render.yaml | 370.0K | 524.9K |
| opus-5-5 | render | crud | 1 | Node.js 20+, Express, PostgreSQL | 498 | 3 | render.yaml | 436.5K | 920.6K |
| opus-5-5 | render | api | 1 | Python 3.12, FastAPI, PostgreSQL | 466 | 6 | render.yaml | 484.4K | 814.7K |
| opus-5-5 | render | dataviz | 1 | Node.js 22, Node.js http | 478 | 0 | render.yaml | 544.4K | 843.1K |
| opus-5-5 | render | realtime | 1 | Node.js 18+, Node.js http | 481 | 1 | render.yaml | 347.9K | 393.9K |
| opus-5-5 | vercel | static | 1 | Node.js 18+, Vercel Functions | 392 | 0 | vercel.json | 459.7K | 316.4K |
| opus-5-5 | vercel | crud | 1 | Node.js 20+, Express | 369 | 3 | vercel.json | 443.0K | 897.7K |
| opus-5-5 | vercel | api | 1 | Node.js 20+, Hono | 671 | 10 | docker-compose.yml | 369.7K | 6.65M |
| opus-5-5 | vercel | dataviz | 1 | Node.js 20+, Vercel Functions | 489 | 0 | vercel.json | 653.4K | 489.5K |
| opus-5-5 | vercel | realtime | 1 | Node.js, Next.js, React | 470 | 4 | — | 545.1K | 955.9K |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security & compliance* is an independent Claude Code review of how each app was deployed, whether its hosting plan fits how the app is used, and what is live, scored against a fixed rubric. *Stack fit* is the same review's rating of the stack the agent chose, judged against the app's requirements. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, are priced on the cheapest plan that allows it. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md#hosting-cost).

## Screenshots

What the verifier saw on each deployment. Each picture links to its cell's report, which has the rest.

| App | Cloudish | DigitalOcean | Railway | Render | Vercel |
|---|---|---|---|---|---|
| Static site | [<img src="cells/opus-5-5/cloudish/static-t1/home.jpg" width="220" alt="Static site on Cloudish">](cells/opus-5-5/cloudish/static-t1.md) | [<img src="cells/opus-5-5/digitalocean/static-t1/home.jpg" width="220" alt="Static site on DigitalOcean">](cells/opus-5-5/digitalocean/static-t1.md) | [<img src="cells/opus-5-5/railway/static-t1/home.jpg" width="220" alt="Static site on Railway">](cells/opus-5-5/railway/static-t1.md) | [<img src="cells/opus-5-5/render/static-t1/home.jpg" width="220" alt="Static site on Render">](cells/opus-5-5/render/static-t1.md) | [<img src="cells/opus-5-5/vercel/static-t1/home.jpg" width="220" alt="Static site on Vercel">](cells/opus-5-5/vercel/static-t1.md) |
| CRUD app | [<img src="cells/opus-5-5/cloudish/crud-t1/signin.jpg" width="220" alt="CRUD app on Cloudish">](cells/opus-5-5/cloudish/crud-t1.md) | [<img src="cells/opus-5-5/digitalocean/crud-t1/signin.jpg" width="220" alt="CRUD app on DigitalOcean">](cells/opus-5-5/digitalocean/crud-t1.md) | [<img src="cells/opus-5-5/railway/crud-t1/signin.jpg" width="220" alt="CRUD app on Railway">](cells/opus-5-5/railway/crud-t1.md) | [<img src="cells/opus-5-5/render/crud-t1/signin.jpg" width="220" alt="CRUD app on Render">](cells/opus-5-5/render/crud-t1.md) | [<img src="cells/opus-5-5/vercel/crud-t1/signin.jpg" width="220" alt="CRUD app on Vercel">](cells/opus-5-5/vercel/crud-t1.md) |
| API | [<img src="cells/opus-5-5/cloudish/api-t1/docs.jpg" width="220" alt="API on Cloudish">](cells/opus-5-5/cloudish/api-t1.md) | [<img src="cells/opus-5-5/digitalocean/api-t1/docs.jpg" width="220" alt="API on DigitalOcean">](cells/opus-5-5/digitalocean/api-t1.md) | [<img src="cells/opus-5-5/railway/api-t1/docs.jpg" width="220" alt="API on Railway">](cells/opus-5-5/railway/api-t1.md) | [<img src="cells/opus-5-5/render/api-t1/docs.jpg" width="220" alt="API on Render">](cells/opus-5-5/render/api-t1.md) | [<img src="cells/opus-5-5/vercel/api-t1/docs.jpg" width="220" alt="API on Vercel">](cells/opus-5-5/vercel/api-t1.md) |
| Dashboard | [<img src="cells/opus-5-5/cloudish/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Cloudish">](cells/opus-5-5/cloudish/dataviz-t1.md) | [<img src="cells/opus-5-5/digitalocean/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on DigitalOcean">](cells/opus-5-5/digitalocean/dataviz-t1.md) | [<img src="cells/opus-5-5/railway/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Railway">](cells/opus-5-5/railway/dataviz-t1.md) | [<img src="cells/opus-5-5/render/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Render">](cells/opus-5-5/render/dataviz-t1.md) | [<img src="cells/opus-5-5/vercel/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Vercel">](cells/opus-5-5/vercel/dataviz-t1.md) |
| Realtime chat | [<img src="cells/opus-5-5/cloudish/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Cloudish">](cells/opus-5-5/cloudish/realtime-t1.md) | [<img src="cells/opus-5-5/digitalocean/realtime-t1/chat.jpg" width="220" alt="Realtime chat on DigitalOcean">](cells/opus-5-5/digitalocean/realtime-t1.md) | [<img src="cells/opus-5-5/railway/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Railway">](cells/opus-5-5/railway/realtime-t1.md) | [<img src="cells/opus-5-5/render/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Render">](cells/opus-5-5/render/realtime-t1.md) | [<img src="cells/opus-5-5/vercel/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Vercel">](cells/opus-5-5/vercel/realtime-t1.md) |
