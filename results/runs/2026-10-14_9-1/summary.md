# Benchmark run 2026-10-14_9-1

- Date: 2026-10-14
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: full
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38499293224

## Summary

| Cloud | Success | Human steps | Human time | Security & compliance | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 5/5 | 0 | 0 min | 79/100 | 99% | 2m 14s | 3m 26s | 7.00M | $4.55 | $0.55 | $39.20 |
| [DigitalOcean](https://www.digitalocean.com) | 5/5 | 3 | 7 min | 85/100 | 100% | 2m 09s | 5m 04s | 4.67M | $3.70 | $39.00 | $39.00 |
| [Render](https://render.com) | 5/5 | 2 | 5 min | 71/100 | 100% | 1m 58s | 5m 26s | 5.35M | $4.29 | $0.00 | $35.65 |
| [Vercel](https://vercel.com) | 5/5 | 2 | 5 min | 76/100 | 100% | 2m 20s | 7m 51s | 13.27M | $7.70 | $60.00 | $100.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site | CRUD app | API | Dashboard | Realtime chat |
|---|---|---|---|---|---|
| Cloudish | ✅ | ✅ | ✅ | ✅ | ✅ |
| DigitalOcean | ✅ | ✅ | ✅ | ✅ | ✅ |
| Render | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vercel | ✅ | ✅ | ✅ | ✅ | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | 0 | 0 min | 82/100 | 1m 47s | 2m 12s | 0s | 1.21M | $0.73 | $0.11 | $7.84 |
| opus-5-5 | cloudish | crud | 1 | [✅ success](cells/opus-5-5/cloudish/crud-t1.md) | 18/19 | 0 | 0 min | 74/100 | 2m 23s | 6m 16s | 0s | 1.77M | $1.16 | $0.11 | $7.84 |
| opus-5-5 | cloudish | api | 1 | [✅ success](cells/opus-5-5/cloudish/api-t1.md) | 20/20 | 0 | 0 min | 77/100 | 3m 09s | 3m 54s | 0s | 1.85M | $1.17 | $0.11 | $7.84 |
| opus-5-5 | cloudish | dataviz | 1 | [✅ success](cells/opus-5-5/cloudish/dataviz-t1.md) | 12/12 | 0 | 0 min | 78/100 | 1m 54s | 2m 14s | 0s | 1.19M | $0.75 | $0.11 | $7.84 |
| opus-5-5 | cloudish | realtime | 1 | [✅ success](cells/opus-5-5/cloudish/realtime-t1.md) | 13/13 | 0 | 0 min | 85/100 | 1m 56s | 2m 36s | 0s | 977.7K | $0.73 | $0.11 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) | 16/16 | 3 | 7 min | 91/100 | 1m 45s | 1m 54s | 0s | 732.6K | $0.51 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | crud | 1 | [✅ success](cells/opus-5-5/digitalocean/crud-t1.md) | 19/19 | 3 | 7 min | 78/100 | 2m 06s | 11m 57s | 0s | 857.1K | $0.81 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | api | 1 | [✅ success](cells/opus-5-5/digitalocean/api-t1.md) | 20/20 | 3 | 7 min | 87/100 | 2m 43s | 8m 12s | 0s | 1.11M | $1.00 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | dataviz | 1 | [✅ success](cells/opus-5-5/digitalocean/dataviz-t1.md) | 12/12 | 3 | 7 min | 84/100 | 2m 38s | 1m 47s | 0s | 1.25M | $0.82 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | realtime | 1 | [✅ success](cells/opus-5-5/digitalocean/realtime-t1.md) | 13/13 | 3 | 7 min | 86/100 | 1m 36s | 1m 30s | 0s | 715.0K | $0.56 | $5.00 | $5.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) | 16/16 | 2 | 5 min | 72/100 | 1m 20s | 1m 22s | 0s | 643.6K | $0.61 | $0.00 | $7.13 |
| opus-5-5 | render | crud | 1 | [✅ success](cells/opus-5-5/render/crud-t1.md) | 19/19 | 2 | 5 min | 62/100 | 1m 58s | 10m 41s | 0s | 1.23M | $0.98 | $0.00 | $7.13 |
| opus-5-5 | render | api | 1 | [✅ success](cells/opus-5-5/render/api-t1.md) | 20/20 | 2 | 5 min | 69/100 | 2m 37s | 11m 14s | 0s | 1.30M | $1.18 | $0.00 | $7.13 |
| opus-5-5 | render | dataviz | 1 | [✅ success](cells/opus-5-5/render/dataviz-t1.md) | 12/12 | 2 | 5 min | 74/100 | 2m 16s | 2m 21s | 0s | 1.50M | $0.93 | $0.00 | $7.13 |
| opus-5-5 | render | realtime | 1 | [✅ success](cells/opus-5-5/render/realtime-t1.md) | 13/13 | 2 | 5 min | 78/100 | 1m 40s | 1m 33s | 0s | 677.6K | $0.59 | $0.00 | $7.13 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 | 5 min | 76/100 | 1m 16s | 1m 02s | 0s | 547.9K | $0.54 | $20.00 | $20.00 |
| opus-5-5 | vercel | crud | 1 | [✅ success](cells/opus-5-5/vercel/crud-t1.md) | 19/19 | 2 | 5 min | 68/100 | 2m 11s | 4m 33s | 0s | 1.78M | $1.20 | $20.00 | $20.00 |
| opus-5-5 | vercel | api | 1 | [✅ success](cells/opus-5-5/vercel/api-t1.md) | 20/20 | 2 | 5 min | 82/100 | 2m 22s | 4m 51s | 0s | 2.02M | $1.33 | $0.00 | $20.00 |
| opus-5-5 | vercel | dataviz | 1 | [✅ success](cells/opus-5-5/vercel/dataviz-t1.md) | 12/12 | 2 | 5 min | 74/100 | 2m 30s | 1m 23s | 0s | 1.29M | $0.84 | $20.00 | $20.00 |
| opus-5-5 | vercel | realtime | 1 | [✅ success](cells/opus-5-5/vercel/realtime-t1.md) | 13/13 | 2 | 5 min | 81/100 | 3m 23s | 27m 29s | 0s | 7.63M | $3.79 | $0.00 | $20.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | Node.js 22, Node.js http | 399 | 0 | Dockerfile, .dockerignore | 384.5K | 830.3K |
| opus-5-5 | cloudish | crud | 1 | Node.js 24, Node.js http, SQLite | 562 | 0 | Dockerfile, .dockerignore | 508.5K | 1.27M |
| opus-5-5 | cloudish | api | 1 | Node.js 24, Node.js http, SQLite | 672 | 0 | Dockerfile, .dockerignore | 744.0K | 1.10M |
| opus-5-5 | cloudish | dataviz | 1 | Node.js 22, Node.js http | 345 | 0 | Dockerfile, .dockerignore | 352.3K | 838.4K |
| opus-5-5 | cloudish | realtime | 1 | Node.js 24, Node.js http, SQLite | 428 | 1 | Dockerfile, .dockerignore | 356.0K | 621.7K |
| opus-5-5 | digitalocean | static | 1 | Node.js 22, Node.js http | 391 | 0 | Dockerfile, .dockerignore, app.yaml | 335.2K | 397.5K |
| opus-5-5 | digitalocean | crud | 1 | Node.js 22, Express, PostgreSQL | 451 | 5 | Dockerfile, .dockerignore, .do/app.yaml | 357.5K | 499.6K |
| opus-5-5 | digitalocean | api | 1 | Node.js 22, Express, PostgreSQL | 533 | 2 | Dockerfile, .dockerignore, .do/app.yaml | 558.9K | 555.3K |
| opus-5-5 | digitalocean | dataviz | 1 | Node.js 22, Express | 481 | 1 | Dockerfile, .dockerignore, app.yaml | 594.0K | 659.1K |
| opus-5-5 | digitalocean | realtime | 1 | Node.js 22, Node.js http | 405 | 1 | Dockerfile, .dockerignore, .do/app.yaml | 345.6K | 369.4K |
| opus-5-5 | render | static | 1 | Node.js 18+, Node.js http | 344 | 0 | render.yaml | 332.8K | 310.9K |
| opus-5-5 | render | crud | 1 | Node.js 22, Express, PostgreSQL | 441 | 3 | render.yaml | 435.0K | 792.0K |
| opus-5-5 | render | api | 1 | Node.js 22, Express, PostgreSQL | 494 | 2 | render.yaml | 458.9K | 837.1K |
| opus-5-5 | render | dataviz | 1 | Node.js 24, Express | 439 | 1 | render.yaml | 582.8K | 921.8K |
| opus-5-5 | render | realtime | 1 | Node.js 20+, Node.js http | 402 | 1 | render.yaml | 339.5K | 338.2K |
| opus-5-5 | vercel | static | 1 | Node.js 18+, Vercel Functions | 373 | 0 | vercel.json | 293.7K | 254.2K |
| opus-5-5 | vercel | crud | 1 | Node.js 24, Express, Vercel Blob | 593 | 4 | vercel.json | 404.8K | 1.38M |
| opus-5-5 | vercel | api | 1 | Node.js 20+, Hono, Vercel Blob | 652 | 4 | vercel.json | 465.3K | 1.55M |
| opus-5-5 | vercel | dataviz | 1 | Node.js 20+, Vercel Functions | 534 | 0 | vercel.json | 742.1K | 544.9K |
| opus-5-5 | vercel | realtime | 1 | Node.js, Next.js, React | 841 | 9 | vercel.json | 744.7K | 6.89M |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security & compliance* is an independent Claude Code review of how each app was deployed, whether its hosting plan fits how the app is used, and what is live, scored against a fixed rubric. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, are priced on the cheapest plan that allows it. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md#hosting-cost).

## Screenshots

What the verifier saw on each deployment. Each picture links to its cell's report, which has the rest.

| App | Cloudish | DigitalOcean | Render | Vercel |
|---|---|---|---|---|
| Static site | [<img src="cells/opus-5-5/cloudish/static-t1/home.jpg" width="220" alt="Static site on Cloudish">](cells/opus-5-5/cloudish/static-t1.md) | [<img src="cells/opus-5-5/digitalocean/static-t1/home.jpg" width="220" alt="Static site on DigitalOcean">](cells/opus-5-5/digitalocean/static-t1.md) | [<img src="cells/opus-5-5/render/static-t1/home.jpg" width="220" alt="Static site on Render">](cells/opus-5-5/render/static-t1.md) | [<img src="cells/opus-5-5/vercel/static-t1/home.jpg" width="220" alt="Static site on Vercel">](cells/opus-5-5/vercel/static-t1.md) |
| CRUD app | — | [<img src="cells/opus-5-5/digitalocean/crud-t1/signin.jpg" width="220" alt="CRUD app on DigitalOcean">](cells/opus-5-5/digitalocean/crud-t1.md) | [<img src="cells/opus-5-5/render/crud-t1/signin.jpg" width="220" alt="CRUD app on Render">](cells/opus-5-5/render/crud-t1.md) | [<img src="cells/opus-5-5/vercel/crud-t1/signin.jpg" width="220" alt="CRUD app on Vercel">](cells/opus-5-5/vercel/crud-t1.md) |
| API | [<img src="cells/opus-5-5/cloudish/api-t1/docs.jpg" width="220" alt="API on Cloudish">](cells/opus-5-5/cloudish/api-t1.md) | [<img src="cells/opus-5-5/digitalocean/api-t1/docs.jpg" width="220" alt="API on DigitalOcean">](cells/opus-5-5/digitalocean/api-t1.md) | [<img src="cells/opus-5-5/render/api-t1/docs.jpg" width="220" alt="API on Render">](cells/opus-5-5/render/api-t1.md) | [<img src="cells/opus-5-5/vercel/api-t1/docs.jpg" width="220" alt="API on Vercel">](cells/opus-5-5/vercel/api-t1.md) |
| Dashboard | [<img src="cells/opus-5-5/cloudish/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Cloudish">](cells/opus-5-5/cloudish/dataviz-t1.md) | [<img src="cells/opus-5-5/digitalocean/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on DigitalOcean">](cells/opus-5-5/digitalocean/dataviz-t1.md) | [<img src="cells/opus-5-5/render/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Render">](cells/opus-5-5/render/dataviz-t1.md) | [<img src="cells/opus-5-5/vercel/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Vercel">](cells/opus-5-5/vercel/dataviz-t1.md) |
| Realtime chat | [<img src="cells/opus-5-5/cloudish/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Cloudish">](cells/opus-5-5/cloudish/realtime-t1.md) | [<img src="cells/opus-5-5/digitalocean/realtime-t1/chat.jpg" width="220" alt="Realtime chat on DigitalOcean">](cells/opus-5-5/digitalocean/realtime-t1.md) | [<img src="cells/opus-5-5/render/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Render">](cells/opus-5-5/render/realtime-t1.md) | [<img src="cells/opus-5-5/vercel/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Vercel">](cells/opus-5-5/vercel/realtime-t1.md) |
