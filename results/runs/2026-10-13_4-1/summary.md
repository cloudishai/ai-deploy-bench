# Benchmark run 2026-10-13_4-1

- Date: 2026-10-13
- Agent: Claude Code 2.1.296
- Models: Opus 5.5
- Scope: apps: static · clouds: all · models: all
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38455576719

## Summary

| Cloud | Success | Human setup | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 1/1 | none | 100% | 2m 06s | 6m 53s | 1.02M | $0.73 | $7.84 |
| [DigitalOcean](https://www.digitalocean.com) | 1/1 | 3 · 7 min | 100% | 1m 31s | 2m 26s | 484.7K | $0.45 | $5.00 |
| [Render](https://render.com) | 1/1 | 2 · 5 min | 100% | 1m 21s | 2m 08s | 537.7K | $0.50 | $0.00 |
| [Vercel](https://vercel.com) | 1/1 | 2 · 5 min | 100% | 1m 25s | 1m 57s | 419.6K | $0.42 | $0.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site |
|---|---|
| Cloudish | ✅ |
| DigitalOcean | ✅ |
| Render | ✅ |
| Vercel | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Build | Deploy | Ready after | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | none | 2m 06s | 6m 53s | 0s | 1.02M | $0.73 | $7.84 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) | 16/16 | 3 · 7 min | 1m 31s | 2m 26s | 0s | 484.7K | $0.45 | $5.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) | 16/16 | 2 · 5 min | 1m 21s | 2m 08s | 0s | 537.7K | $0.50 | $0.00 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 · 5 min | 1m 25s | 1m 57s | 0s | 419.6K | $0.42 | $0.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Stack | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | — | 452 | 0 | Dockerfile, .dockerignore | 277.1K | 747.6K |
| opus-5-5 | digitalocean | static | 1 | — | 386 | 0 | Dockerfile, .dockerignore, .do/app.yaml | 211.2K | 273.5K |
| opus-5-5 | render | static | 1 | — | 371 | 0 | render.yaml | 183.7K | 354.0K |
| opus-5-5 | vercel | static | 1 | — | 395 | 0 | vercel.json | 211.0K | 208.6K |

*Human setup* counts the distinct steps a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), with estimated minutes; see the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the resources left running, priced as always-on (730 h) with light traffic; usage-billed and free-tier resources can cost less in practice. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md).
