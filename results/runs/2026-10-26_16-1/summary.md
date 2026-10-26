# Benchmark run 2026-10-26_16-1

- Date: 2026-10-26
- Benchmark version: 3 ([changes](../../../CHANGES.md))
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: full
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/40387893074

## Summary

| Cloud | Success | Deploys without human | Human steps | Human time | Security & compliance | Stack fit | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 4/5 | 4/5 | 0 | 0 min | 81/100 | 91/100 | 99% | 2m 25s | 3m 37s | 7.05M | $4.72 | $0.55 | $39.20 |
| [DigitalOcean](https://www.digitalocean.com) | 5/5 | 0/5 | 3 | 7 min | 84/100 | 85/100 | 100% | 2m 03s | 4m 30s | 5.64M | $4.52 | $39.00 | $39.00 |
| [Railway](https://railway.com) | 0/5 | 0/5 | 3 | 7 min | — | — | 0% | 2m 13s | 4m 51s | 7.05M | $4.72 | $0.00 | $0.00 |
| [Render](https://render.com) | 5/5 | 0/5 | 2 | 5 min | 70/100 | 80/100 | 100% | 2m 03s | 3m 52s | 7.00M | $4.97 | $0.00 | $35.65 |
| [Vercel](https://vercel.com) | 3/5 | 0/5 | 3 | 8 min | 77/100 | 78/100 | 76% | 2m 24s | 2m 21s | 14.06M | $8.27 | $60.00 | $100.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site | CRUD app | API | Dashboard | Realtime chat |
|---|---|---|---|---|---|
| Cloudish | ✅ | ✅ | ⚠️ 19/20 | ✅ | ✅ |
| DigitalOcean | ✅ | ✅ | ✅ | ✅ | ✅ |
| Railway | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person | 🙋 needs a person |
| Render | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vercel | ✅ | 🙋 needs a person | 🙋 needs a person | ✅ | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Stack fit | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | 0 | 0 min | 84/100 | 93/100 | 1m 34s | 2m 18s | 0s | 758.1K | $0.59 | $0.11 | $7.84 |
| opus-5-5 | cloudish | crud | 1 | [✅ success](cells/opus-5-5/cloudish/crud-t1.md) | 19/19 | 0 | 0 min | 74/100 | 87/100 | 2m 30s | 6m 44s | 0s | 1.81M | $1.19 | $0.11 | $7.84 |
| opus-5-5 | cloudish | api | 1 | [⚠️ partial](cells/opus-5-5/cloudish/api-t1.md) | 19/20 | 0 | 0 min | 80/100 | 90/100 | 3m 04s | 4m 22s | 0s | 1.77M | $1.12 | $0.11 | $7.84 |
| opus-5-5 | cloudish | dataviz | 1 | [✅ success](cells/opus-5-5/cloudish/dataviz-t1.md) | 12/12 | 0 | 0 min | 82/100 | 97/100 | 2m 38s | 2m 19s | 0s | 1.55M | $0.97 | $0.11 | $7.84 |
| opus-5-5 | cloudish | realtime | 1 | [✅ success](cells/opus-5-5/cloudish/realtime-t1.md) | 13/13 | 0 | 0 min | 84/100 | 90/100 | 2m 21s | 2m 20s | 0s | 1.16M | $0.86 | $0.11 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) | 16/16 | 3 | 7 min | 87/100 | 84/100 | 1m 40s | 2m 10s | 0s | 1.09M | $0.84 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | crud | 1 | [✅ success](cells/opus-5-5/digitalocean/crud-t1.md) | 19/19 | 3 | 7 min | 79/100 | 87/100 | 2m 24s | 7m 19s | 0s | 1.16M | $1.05 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | api | 1 | [✅ success](cells/opus-5-5/digitalocean/api-t1.md) | 20/20 | 3 | 7 min | 81/100 | 87/100 | 2m 21s | 9m 00s | 0s | 1.15M | $1.01 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | dataviz | 1 | [✅ success](cells/opus-5-5/digitalocean/dataviz-t1.md) | 12/12 | 3 | 7 min | 89/100 | 90/100 | 2m 11s | 2m 08s | 0s | 1.39M | $0.93 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | realtime | 1 | [✅ success](cells/opus-5-5/digitalocean/realtime-t1.md) | 13/13 | 3 | 7 min | 84/100 | 79/100 | 1m 39s | 1m 51s | 0s | 847.9K | $0.69 | $5.00 | $5.00 |
| opus-5-5 | railway | static | 1 | [❌ failed](cells/opus-5-5/railway/static-t1.md) | 0/0 | 2 | 5 min | — | — | 1m 32s | 10m 01s | — | 1.37M | $0.88 | $0.00 | $0.00 |
| opus-5-5 | railway | crud | 1 | [❌ failed](cells/opus-5-5/railway/crud-t1.md) | 0/0 | 2 | 5 min | — | — | 2m 19s | 40s | — | 1.26M | $0.81 | $0.00 | $0.00 |
| opus-5-5 | railway | api | 1 | [❌ failed](cells/opus-5-5/railway/api-t1.md) | 0/0 | 3 | 7 min | — | — | 2m 10s | 2m 30s | — | 1.21M | $0.83 | $0.00 | $0.00 |
| opus-5-5 | railway | dataviz | 1 | [❌ failed](cells/opus-5-5/railway/dataviz-t1.md) | 0/0 | 2 | 5 min | — | — | 2m 36s | 10m 27s | — | 1.99M | $1.37 | $0.00 | $0.00 |
| opus-5-5 | railway | realtime | 1 | [❌ failed](cells/opus-5-5/railway/realtime-t1.md) | 0/0 | 2 | 5 min | — | — | 2m 27s | 38s | — | 1.21M | $0.84 | $0.00 | $0.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) | 16/16 | 2 | 5 min | 72/100 | 81/100 | 1m 36s | 2m 22s | 0s | 1.07M | $0.80 | $0.00 | $7.13 |
| opus-5-5 | render | crud | 1 | [✅ success](cells/opus-5-5/render/crud-t1.md) | 19/19 | 2 | 5 min | 64/100 | 80/100 | 2m 12s | 4m 44s | 0s | 1.71M | $1.17 | $0.00 | $7.13 |
| opus-5-5 | render | api | 1 | [✅ success](cells/opus-5-5/render/api-t1.md) | 20/20 | 2 | 5 min | 68/100 | 81/100 | 2m 30s | 5m 57s | 0s | 1.61M | $1.13 | $0.00 | $7.13 |
| opus-5-5 | render | dataviz | 1 | [✅ success](cells/opus-5-5/render/dataviz-t1.md) | 12/12 | 2 | 5 min | 69/100 | 81/100 | 2m 15s | 4m 35s | 0s | 1.62M | $1.04 | $0.00 | $7.13 |
| opus-5-5 | render | realtime | 1 | [✅ success](cells/opus-5-5/render/realtime-t1.md) | 13/13 | 2 | 5 min | 78/100 | 76/100 | 1m 43s | 1m 41s | 0s | 986.1K | $0.83 | $0.00 | $7.13 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 | 5 min | 78/100 | 100/100 | 1m 31s | 1m 02s | 0s | 1.64M | $1.10 | $20.00 | $20.00 |
| opus-5-5 | vercel | crud | 1 | [⚠️ partial](cells/opus-5-5/vercel/crud-t1.md) | 6/19 | 3 | 8 min | 65/100 | 80/100 | 2m 08s | 1m 27s | 0s | 1.62M | $0.99 | $20.00 | $20.00 |
| opus-5-5 | vercel | api | 1 | [⚠️ partial](cells/opus-5-5/vercel/api-t1.md) | 10/20 | 3 | 8 min | 82/100 | 55/100 | 2m 41s | 3m 25s | 0s | 2.57M | $1.84 | $0.00 | $20.00 |
| opus-5-5 | vercel | dataviz | 1 | [✅ success](cells/opus-5-5/vercel/dataviz-t1.md) | 12/12 | 2 | 5 min | 75/100 | 93/100 | 2m 34s | 1m 00s | 0s | 2.09M | $1.19 | $20.00 | $20.00 |
| opus-5-5 | vercel | realtime | 1 | [✅ success](cells/opus-5-5/vercel/realtime-t1.md) | 13/13 | 2 | 5 min | 82/100 | 60/100 | 3m 05s | 4m 49s | 0s | 6.14M | $3.14 | $0.00 | $20.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | Node.js 24, Node.js http | 355 | 0 | Dockerfile, .dockerignore | 270.3K | 487.8K |
| opus-5-5 | cloudish | crud | 1 | Node.js 24, Node.js http, SQLite | 532 | 0 | Dockerfile, .dockerignore | 470.1K | 1.34M |
| opus-5-5 | cloudish | api | 1 | Python 3.12, FastAPI, SQLite | 323 | 4 | Dockerfile, .dockerignore | 738.0K | 1.03M |
| opus-5-5 | cloudish | dataviz | 1 | Node.js 20, Node.js http | 505 | 0 | Dockerfile, .dockerignore | 706.3K | 845.2K |
| opus-5-5 | cloudish | realtime | 1 | Node.js 24, Node.js http, SQLite | 431 | 1 | Dockerfile, .dockerignore | 409.2K | 749.5K |
| opus-5-5 | digitalocean | static | 1 | Node.js 22, Node.js http | 434 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 455.3K | 360.6K |
| opus-5-5 | digitalocean | crud | 1 | Node.js 22, Express, PostgreSQL | 472 | 3 | Dockerfile, .dockerignore, .do/app.yaml | 491.3K | 353.6K |
| opus-5-5 | digitalocean | api | 1 | Python 3.12, FastAPI, PostgreSQL | 358 | 6 | Dockerfile, .dockerignore | 438.4K | 401.5K |
| opus-5-5 | digitalocean | dataviz | 1 | Node.js 20, Node.js http | 540 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 645.9K | 448.4K |
| opus-5-5 | digitalocean | realtime | 1 | Node.js 20, Node.js http | 442 | 1 | Dockerfile, .dockerignore, .do/app.yaml | 343.9K | 264.1K |
| opus-5-5 | railway | static | 1 | Node.js 18+, Node.js http | 404 | 0 | railway.json | 382.7K | 770.2K |
| opus-5-5 | railway | crud | 1 | Node.js 20+, Express | 488 | 3 | railway.json | 482.8K | 381.0K |
| opus-5-5 | railway | api | 1 | Node.js 20+, Express | 466 | 2 | railway.json | 407.4K | 609.0K |
| opus-5-5 | railway | dataviz | 1 | Node.js 20+, Node.js http | 534 | 0 | railway.json | 724.9K | 950.9K |
| opus-5-5 | railway | realtime | 1 | Node.js 20+, Node.js http | 450 | 2 | railway.json | 498.9K | 403.2K |
| opus-5-5 | render | static | 1 | Node.js 24, Node.js http | 421 | 0 | render.yaml | 370.0K | 524.9K |
| opus-5-5 | render | crud | 1 | Node.js 20+, Express, PostgreSQL | 498 | 3 | render.yaml | 436.5K | 920.6K |
| opus-5-5 | render | api | 1 | Python 3.12, FastAPI, PostgreSQL | 466 | 6 | render.yaml | 484.4K | 814.7K |
| opus-5-5 | render | dataviz | 1 | Node.js 22, Node.js http | 478 | 0 | render.yaml | 544.4K | 843.1K |
| opus-5-5 | render | realtime | 1 | Node.js 18+, Node.js http | 481 | 1 | render.yaml | 347.9K | 393.9K |
| opus-5-5 | vercel | static | 1 | Node.js 18+, Vercel Functions | 406 | 0 | vercel.json | 379.5K | 391.0K |
| opus-5-5 | vercel | crud | 1 | Node.js 20+, Express | 426 | 4 | vercel.json | 400.9K | 605.2K |
| opus-5-5 | vercel | api | 1 | Node.js 20+, Hono | 688 | 3 | — | 560.4K | 1.46M |
| opus-5-5 | vercel | dataviz | 1 | Node.js 18+, Vercel Functions | 475 | 0 | vercel.json | 623.2K | 446.0K |
| opus-5-5 | vercel | realtime | 1 | Node.js, Next.js, React | 836 | 6 | — | 564.3K | 1.51M |

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
