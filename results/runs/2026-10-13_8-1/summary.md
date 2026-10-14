# Benchmark run 2026-10-13_8-1

- Date: 2026-10-13
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: full
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38480665016

## Summary

| Cloud | Success | Human steps | Human time | Security & compliance | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 5/5 | 0 | 0 min | 78/100 | 100% | 2m 04s | 2m 48s | 5.47M | $3.78 | $0.55 | $39.20 |
| [DigitalOcean](https://www.digitalocean.com) | 4/5 | 3 | 7 min | 85/100 | 99% | 2m 10s | 4m 54s | 4.15M | $3.60 | $39.00 | $39.00 |
| [Render](https://render.com) | 5/5 | 2 | 5 min | 69/100 | 100% | 2m 11s | 3m 46s | 5.55M | $4.13 | $0.00 | $35.65 |
| [Vercel](https://vercel.com) | 4/5 | 3 | 8 min | 76/100 | 91% | 2m 39s | 4m 41s | 7.95M | $5.37 | $60.00 | $100.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site | CRUD app | API | Dashboard | Realtime chat |
|---|---|---|---|---|---|
| Cloudish | ✅ | ✅ | ✅ | ✅ | ✅ |
| DigitalOcean | ✅ | ✅ | ⚠️ 19/20 | ✅ | ✅ |
| Render | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vercel | ✅ | ✅ | 🙋 needs a person | ✅ | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security & compliance | Build | Deploy | Ready after | Tokens | Agent cost | Hosting, light use | Hosting, busy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | 0 | 0 min | 75/100 | 1m 17s | 2m 41s | 0s | 833.2K | $0.57 | $0.11 | $7.84 |
| opus-5-5 | cloudish | crud | 1 | [✅ success](cells/opus-5-5/cloudish/crud-t1.md) | 19/19 | 0 | 0 min | 76/100 | 1m 51s | 4m 09s | 0s | 980.1K | $0.73 | $0.11 | $7.84 |
| opus-5-5 | cloudish | api | 1 | [✅ success](cells/opus-5-5/cloudish/api-t1.md) | 20/20 | 0 | 0 min | 80/100 | 2m 09s | 2m 25s | 0s | 1.14M | $0.81 | $0.11 | $7.84 |
| opus-5-5 | cloudish | dataviz | 1 | [✅ success](cells/opus-5-5/cloudish/dataviz-t1.md) | 12/12 | 0 | 0 min | 80/100 | 2m 57s | 2m 26s | 0s | 1.53M | $0.94 | $0.11 | $7.84 |
| opus-5-5 | cloudish | realtime | 1 | [✅ success](cells/opus-5-5/cloudish/realtime-t1.md) | 13/13 | 0 | 0 min | 80/100 | 2m 07s | 2m 16s | 0s | 995.5K | $0.73 | $0.11 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) | 16/16 | 3 | 7 min | 89/100 | 1m 28s | 1m 38s | 0s | 650.9K | $0.61 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | crud | 1 | [✅ success](cells/opus-5-5/digitalocean/crud-t1.md) | 19/19 | 3 | 7 min | 78/100 | 2m 20s | 11m 57s | 0s | 864.4K | $0.81 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | api | 1 | [⚠️ partial](cells/opus-5-5/digitalocean/api-t1.md) | 19/20 | 3 | 7 min | 84/100 | 2m 44s | 8m 07s | 0s | 941.2K | $0.91 | $12.00 | $12.00 |
| opus-5-5 | digitalocean | dataviz | 1 | [✅ success](cells/opus-5-5/digitalocean/dataviz-t1.md) | 12/12 | 3 | 7 min | 88/100 | 2m 36s | 1m 26s | 0s | 1.09M | $0.73 | $5.00 | $5.00 |
| opus-5-5 | digitalocean | realtime | 1 | [✅ success](cells/opus-5-5/digitalocean/realtime-t1.md) | 13/13 | 3 | 7 min | 86/100 | 1m 45s | 1m 22s | 0s | 608.7K | $0.53 | $5.00 | $5.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) | 16/16 | 2 | 5 min | 72/100 | 1m 45s | 1m 52s | 0s | 866.1K | $0.76 | $0.00 | $7.13 |
| opus-5-5 | render | crud | 1 | [✅ success](cells/opus-5-5/render/crud-t1.md) | 19/19 | 2 | 5 min | 60/100 | 2m 06s | 7m 07s | 0s | 1.28M | $0.89 | $0.00 | $7.13 |
| opus-5-5 | render | api | 1 | [✅ success](cells/opus-5-5/render/api-t1.md) | 20/20 | 2 | 5 min | 72/100 | 2m 20s | 4m 52s | 0s | 1.15M | $0.93 | $0.00 | $7.13 |
| opus-5-5 | render | dataviz | 1 | [✅ success](cells/opus-5-5/render/dataviz-t1.md) | 12/12 | 2 | 5 min | 73/100 | 1m 56s | 2m 25s | 0s | 1.13M | $0.74 | $0.00 | $7.13 |
| opus-5-5 | render | realtime | 1 | [✅ success](cells/opus-5-5/render/realtime-t1.md) | 13/13 | 2 | 5 min | 68/100 | 2m 49s | 2m 34s | 0s | 1.12M | $0.81 | $0.00 | $7.13 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 | 5 min | 74/100 | 1m 22s | 1m 04s | 0s | 421.7K | $0.49 | $20.00 | $20.00 |
| opus-5-5 | vercel | crud | 1 | [✅ success](cells/opus-5-5/vercel/crud-t1.md) | 19/19 | 2 | 5 min | 66/100 | 2m 04s | 4m 56s | 0s | 1.94M | $1.22 | $20.00 | $20.00 |
| opus-5-5 | vercel | api | 1 | [⚠️ partial](cells/opus-5-5/vercel/api-t1.md) | 11/20 | 3 | 8 min | 80/100 | 2m 32s | 6m 56s | 0s | 2.02M | $1.34 | $0.00 | $20.00 |
| opus-5-5 | vercel | dataviz | 1 | [✅ success](cells/opus-5-5/vercel/dataviz-t1.md) | 12/12 | 2 | 5 min | 73/100 | 2m 14s | 1m 03s | 0s | 1.00M | $0.73 | $20.00 | $20.00 |
| opus-5-5 | vercel | realtime | 1 | [✅ success](cells/opus-5-5/vercel/realtime-t1.md) | 13/13 | 2 | 5 min | 84/100 | 5m 02s | 9m 27s | 0s | 2.57M | $1.58 | $0.00 | $20.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Technologies | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | Node.js 22, Node.js http | 289 | 0 | Dockerfile, .dockerignore | 225.2K | 608.0K |
| opus-5-5 | cloudish | crud | 1 | Node.js 24, Express, SQLite | 377 | 2 | Dockerfile, .dockerignore | 394.9K | 585.3K |
| opus-5-5 | cloudish | api | 1 | Python 3.12, FastAPI, SQLite | 419 | 5 | Dockerfile, .dockerignore | 358.3K | 780.3K |
| opus-5-5 | cloudish | dataviz | 1 | Node.js 22, Node.js http | 492 | 0 | Dockerfile, .dockerignore | 591.9K | 934.0K |
| opus-5-5 | cloudish | realtime | 1 | Node.js 22, Node.js http, Files on a persistent volume | 496 | 1 | Dockerfile, .dockerignore | 423.0K | 572.6K |
| opus-5-5 | digitalocean | static | 1 | Node.js 22, Node.js http | 425 | 0 | Dockerfile, .dockerignore, app.yaml | 297.8K | 353.1K |
| opus-5-5 | digitalocean | crud | 1 | Node.js 22, Express, PostgreSQL | 458 | 3 | Dockerfile, .dockerignore, .do/app.yaml | 406.4K | 458.0K |
| opus-5-5 | digitalocean | api | 1 | Node.js 22, Express, PostgreSQL | 574 | 3 | Dockerfile, .dockerignore, .do/app.yaml | 511.3K | 429.9K |
| opus-5-5 | digitalocean | dataviz | 1 | Node.js 22, Node.js http | 477 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 578.9K | 510.4K |
| opus-5-5 | digitalocean | realtime | 1 | Node.js 22, Express | 412 | 2 | Dockerfile, .dockerignore, .do/app.yaml | 332.0K | 276.7K |
| opus-5-5 | render | static | 1 | Node.js 22, Node.js http | 459 | 0 | render.yaml | 340.0K | 526.1K |
| opus-5-5 | render | crud | 1 | Node.js 22, Express, PostgreSQL | 373 | 3 | render.yaml | 395.1K | 889.1K |
| opus-5-5 | render | api | 1 | Node.js 22, Express, PostgreSQL | 458 | 2 | render.yaml | 328.9K | 817.3K |
| opus-5-5 | render | dataviz | 1 | Node.js 24, Express | 337 | 2 | render.yaml | 508.5K | 622.1K |
| opus-5-5 | render | realtime | 1 | Node.js 20+, Node.js http, PostgreSQL | 569 | 2 | render.yaml | 580.8K | 538.3K |
| opus-5-5 | vercel | static | 1 | Node.js 18+, Vercel Functions | 365 | 0 | vercel.json | 254.8K | 167.0K |
| opus-5-5 | vercel | crud | 1 | Node.js 20+, Express, Vercel Blob | 561 | 4 | vercel.json | 407.5K | 1.53M |
| opus-5-5 | vercel | api | 1 | Node.js 20+, Express, Vercel Blob | 693 | 4 | vercel.json | 421.0K | 1.60M |
| opus-5-5 | vercel | dataviz | 1 | Node.js 18+, Vercel Functions | 491 | 0 | vercel.json | 591.4K | 410.2K |
| opus-5-5 | vercel | realtime | 1 | Node.js, Next.js, React | 540 | 9 | vercel.json | 582.9K | 1.99M |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security & compliance* is an independent Claude Code review of how each app was deployed, whether its hosting plan fits how the app is used, and what is live, scored against a fixed rubric. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the deployed resources at two levels of traffic: *light use* is a few visits a week, and *busy* is a public app that crawlers, monitors and visitors hit around the clock. Plans that a business's app can't use under their terms, or that the traffic would exceed, are priced on the cheapest plan that allows it. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md#hosting-cost).

## Screenshots

What the verifier saw on each deployment. Each picture links to its cell's report, which has the rest.

| App | Cloudish | DigitalOcean | Render | Vercel |
|---|---|---|---|---|
| Static site | [<img src="cells/opus-5-5/cloudish/static-t1/home.jpg" width="220" alt="Static site on Cloudish">](cells/opus-5-5/cloudish/static-t1.md) | [<img src="cells/opus-5-5/digitalocean/static-t1/home.jpg" width="220" alt="Static site on DigitalOcean">](cells/opus-5-5/digitalocean/static-t1.md) | [<img src="cells/opus-5-5/render/static-t1/home.jpg" width="220" alt="Static site on Render">](cells/opus-5-5/render/static-t1.md) | [<img src="cells/opus-5-5/vercel/static-t1/home.jpg" width="220" alt="Static site on Vercel">](cells/opus-5-5/vercel/static-t1.md) |
| CRUD app | [<img src="cells/opus-5-5/cloudish/crud-t1/signin.jpg" width="220" alt="CRUD app on Cloudish">](cells/opus-5-5/cloudish/crud-t1.md) | [<img src="cells/opus-5-5/digitalocean/crud-t1/signin.jpg" width="220" alt="CRUD app on DigitalOcean">](cells/opus-5-5/digitalocean/crud-t1.md) | [<img src="cells/opus-5-5/render/crud-t1/signin.jpg" width="220" alt="CRUD app on Render">](cells/opus-5-5/render/crud-t1.md) | [<img src="cells/opus-5-5/vercel/crud-t1/signin.jpg" width="220" alt="CRUD app on Vercel">](cells/opus-5-5/vercel/crud-t1.md) |
| API | [<img src="cells/opus-5-5/cloudish/api-t1/docs.jpg" width="220" alt="API on Cloudish">](cells/opus-5-5/cloudish/api-t1.md) | [<img src="cells/opus-5-5/digitalocean/api-t1/docs.jpg" width="220" alt="API on DigitalOcean">](cells/opus-5-5/digitalocean/api-t1.md) | [<img src="cells/opus-5-5/render/api-t1/docs.jpg" width="220" alt="API on Render">](cells/opus-5-5/render/api-t1.md) | [<img src="cells/opus-5-5/vercel/api-t1/docs.jpg" width="220" alt="API on Vercel">](cells/opus-5-5/vercel/api-t1.md) |
| Dashboard | [<img src="cells/opus-5-5/cloudish/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Cloudish">](cells/opus-5-5/cloudish/dataviz-t1.md) | [<img src="cells/opus-5-5/digitalocean/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on DigitalOcean">](cells/opus-5-5/digitalocean/dataviz-t1.md) | [<img src="cells/opus-5-5/render/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Render">](cells/opus-5-5/render/dataviz-t1.md) | [<img src="cells/opus-5-5/vercel/dataviz-t1/dashboard.jpg" width="220" alt="Dashboard on Vercel">](cells/opus-5-5/vercel/dataviz-t1.md) |
| Realtime chat | [<img src="cells/opus-5-5/cloudish/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Cloudish">](cells/opus-5-5/cloudish/realtime-t1.md) | [<img src="cells/opus-5-5/digitalocean/realtime-t1/chat.jpg" width="220" alt="Realtime chat on DigitalOcean">](cells/opus-5-5/digitalocean/realtime-t1.md) | [<img src="cells/opus-5-5/render/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Render">](cells/opus-5-5/render/realtime-t1.md) | [<img src="cells/opus-5-5/vercel/realtime-t1/chat.jpg" width="220" alt="Realtime chat on Vercel">](cells/opus-5-5/vercel/realtime-t1.md) |
