# Benchmark run 2026-10-13_3-1

- Date: 2026-10-13
- Agent: Claude Code 2.1.296
- Models: Opus 5.5
- Scope: apps: static · clouds: all · models: all
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38446498934

## Summary

| Cloud | Success | Human setup | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 0/1 | none | 0% | 2s | 2s | 0 | $0.00 | $0.00+ |
| [DigitalOcean](https://www.digitalocean.com) | 0/1 | 3 · 7 min | 0% | 1s | 1s | 0 | $0.00 | $0.00 |
| [Render](https://render.com) | 0/1 | 2 · 5 min | 0% | 1s | 1s | 0 | $0.00 | $0.00 |
| [Vercel](https://vercel.com) | 0/1 | 2 · 5 min | 0% | 1s | 1s | 0 | $0.00 | $0.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · ❔ no result

| Cloud | Static site |
|---|---|
| Cloudish | ❌ build |
| DigitalOcean | ❌ build |
| Render | ❌ build |
| Vercel | ❌ build |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Build | Deploy | Ready after | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [❌ failed](cells/opus-5-5/cloudish/static-t1.md) | 0/0 | none | 2s | 2s | — | 0 | $0.00 | — |
| opus-5-5 | digitalocean | static | 1 | [❌ failed](cells/opus-5-5/digitalocean/static-t1.md) | 0/0 | 3 · 7 min | 1s | 1s | — | 0 | $0.00 | $0.00 |
| opus-5-5 | render | static | 1 | [❌ failed](cells/opus-5-5/render/static-t1.md) | 0/0 | 2 · 5 min | 1s | 1s | — | 0 | $0.00 | $0.00 |
| opus-5-5 | vercel | static | 1 | [❌ failed](cells/opus-5-5/vercel/static-t1.md) | 0/0 | 2 · 5 min | 1s | 1s | — | 0 | $0.00 | $0.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Stack | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | — | 0 | 0 | — | 0 | 0 |
| opus-5-5 | digitalocean | static | 1 | — | 0 | 0 | — | 0 | 0 |
| opus-5-5 | render | static | 1 | — | 0 | 0 | — | 0 | 0 |
| opus-5-5 | vercel | static | 1 | — | 0 | 0 | — | 0 | 0 |

*Human setup* counts the distinct steps a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), with estimated minutes; see the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the resources left running, priced as always-on (730 h) with light traffic; usage-billed and free-tier resources can cost less in practice. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md).
