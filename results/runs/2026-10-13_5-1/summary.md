# Benchmark run 2026-10-13_5-1

- Date: 2026-10-13
- Agent: Claude Code 2.1.296
- Models: Opus 5.5 · medium effort · HIPAA organization
- Scope: apps: static · clouds: all · models: all
- Trials per cell: 1
- Workflow run: https://github.com/cloudishai/ai-deploy-bench/actions/runs/38465347915

## Summary

| Cloud | Success | Human steps | Human time | Security | Checks passed | Avg build | Avg deploy | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|---|---|
| [Cloudish](https://cloudish.ai) | 1/1 | 0 | 0 min | 83/100 | 100% | 1m 18s | 3m 38s | 726.0K | $0.52 | $21.66 |
| [DigitalOcean](https://www.digitalocean.com) | 1/1 | 3 | 7 min | 80/100 | 100% | 1m 26s | 2m 18s | 646.6K | $0.48 | $5.00 |
| [Render](https://render.com) | 1/1 | 2 | 5 min | 74/100 | 100% | 1m 20s | 2m 44s | 1.16M | $0.81 | $0.00 |
| [Vercel](https://vercel.com) | 1/1 | 2 | 5 min | 73/100 | 100% | 1m 14s | 1m 49s | 594.9K | $0.57 | $0.00 |

## By app

✅ success · ⚠️ deployed but some required checks failed (checks passed shown) · 🙋 blocked on something only a person can do · ❌ failed (stage shown) · 💥 the agent couldn't run (stage shown) · ❔ no result

| Cloud | Static site |
|---|---|
| Cloudish | ✅ |
| DigitalOcean | ✅ |
| Render | ✅ |
| Vercel | ✅ |

## All cells

| Model | Cloud | App | Trial | Result | Checks | Human steps | Human time | Security | Build | Deploy | Ready after | Tokens | Agent cost | Hosting / month |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | [✅ success](cells/opus-5-5/cloudish/static-t1.md) | 16/16 | 0 | 0 min | 83/100 | 1m 18s | 3m 38s | 0s | 726.0K | $0.52 | $21.66 |
| opus-5-5 | digitalocean | static | 1 | [✅ success](cells/opus-5-5/digitalocean/static-t1.md) | 16/16 | 3 | 7 min | 80/100 | 1m 26s | 2m 18s | 0s | 646.6K | $0.48 | $5.00 |
| opus-5-5 | render | static | 1 | [✅ success](cells/opus-5-5/render/static-t1.md) | 16/16 | 2 | 5 min | 74/100 | 1m 20s | 2m 44s | 0s | 1.16M | $0.81 | $0.00 |
| opus-5-5 | vercel | static | 1 | [✅ success](cells/opus-5-5/vercel/static-t1.md) | 16/16 | 2 | 5 min | 73/100 | 1m 14s | 1m 49s | 0s | 594.9K | $0.57 | $0.00 |

## What was built

Every cell builds its app from scratch for its cloud, so stacks differ by platform.

| Model | Cloud | App | Trial | Stack | Code lines | Dependencies | Deploy config | Build tokens | Deploy tokens |
|---|---|---|---|---|---|---|---|---|---|
| opus-5-5 | cloudish | static | 1 | — | 282 | 0 | Dockerfile, .dockerignore | 185.1K | 541.0K |
| opus-5-5 | digitalocean | static | 1 | — | 392 | 0 | Dockerfile, .dockerignore, app.yaml | 255.8K | 390.8K |
| opus-5-5 | render | static | 1 | — | 417 | 0 | render.yaml | 297.2K | 866.2K |
| opus-5-5 | vercel | static | 1 | — | 368 | 0 | vercel.json | 253.9K | 340.9K |

*Human steps* counts the distinct things a person had to do, or would have to do, for the agent's deployments to work (account setup, terms, payment, Git hosting), and *human time* estimates how long they take. *Security* is an independent Claude Code review of how each app was deployed and what is live, scored against a fixed rubric. See the methodology. Times are wall-clock time of the agent's build and deploy phases; *ready after* is how much longer the app took to answer once the agent finished. Tokens include cache reads and writes. Agent cost is the API cost reported by Claude Code. Hosting is the estimated monthly cost of the resources left running, priced as always-on (730 h) with light traffic; usage-billed and free-tier resources can cost less in practice. `+` means some values were unknown. See [docs/methodology.md](../../../docs/methodology.md).
