# Results

One folder per benchmark run under [`runs/`](runs), newest first. Each has a `summary.md`, a machine-readable `summary.json`, and a record (`<app>-t<trial>.json`) and report (`.md`) per cell under `cells/<model>/<cloud>/`. [`index.json`](index.json) lists every run for tools that read the results.

Only full runs (every cloud, app and model) update the summary in the repository's README.

| Run | Scope | Models | Success | Checks passed | Agent cost |
|---|---|---|---|---|---|
| [2026-10-15 · #14](runs/2026-10-15_14-1/summary.md) | full (clouds: railway rerun on 2026-10-14 · #13) | opus-5-5 | 19/25 | 77% | $29.23 |
| [2026-10-14 · #13](runs/2026-10-14_13-1/summary.md) | full | opus-5-5 | 20/25 | 81% | $29.09 |
| [2026-10-14 · #10](runs/2026-10-14_10-1/summary.md) | full | opus-5-5 | 18/20 | 95% | $15.56 |
| [2026-10-14 · #9](runs/2026-10-14_9-1/summary.md) | full | opus-5-5 | 20/20 | 100% | $20.24 |
| [2026-10-13 · #8](runs/2026-10-13_8-1/summary.md) | full | opus-5-5 | 18/20 | 98% | $16.87 |
| [2026-10-13 · #5](runs/2026-10-13_5-1/summary.md) | apps: static · clouds: all · models: all | opus-5-5 | 4/4 | 100% | $2.38 |
| [2026-10-13 · #4](runs/2026-10-13_4-1/summary.md) | apps: static · clouds: all · models: all | opus-5-5 | 4/4 | 100% | $2.10 |
