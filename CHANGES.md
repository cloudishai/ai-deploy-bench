# Changes

The benchmark has a version, `version` in [`benchmark.yaml`](benchmark.yaml), raised whenever a
change means results aren't comparable with earlier runs: a different prompt, rubric, app or check.
Each run records the version it ran under (`benchmark_version` in its `summary.json` and cell
records), and the summaries and the site show it. Compare metrics only between runs of the same
version.

Changes to the result files themselves are tracked separately, by the schema number described in
[docs/methodology.md](docs/methodology.md#result-files).

## Version 2

**Agents choose their stack deliberately, and the choice is rated.**

### Why

In every run of version 1, every app on every cloud was built with Node.js, about half of them on
the bare `node:http` module, whatever the app. Some choices fit the job poorly but still passed every
check: the static site ran as an always-on container on clouds that offer free static hosting, and
two Vercel apps used Vercel Blob, file storage, as their database. The build prompt only asked for "a
stack and project layout that suit how the cloud runs applications", which any Node server satisfies,
and nothing measured whether the stack suited the app.

The benchmark should let the agent choose its stack freely, since choosing well is part of what it
measures, while making sure it actually makes a choice and showing how good that choice was.

### What changed

- **Build prompt.** Before writing any code, the agent compares the two or three most plausible
  options for the app on the target cloud (in language, framework, data store or hosting model),
  and records them and its choice in `STACK.md`. The prompt states that there is no default
  language or framework, and the environment line lists every language the runner has (Node.js,
  Python, Go, Java, Ruby, PHP, .NET) instead of only Node.js and Python. No technology is suggested
  for any app.
- **Stack fit score.** The independent reviewer, in the same session as the security review, rates
  the stack against a new `stack_rubric`: *fit for the job* (40), *proportion* (30) and *platform
  fit* (30). It judges the stack against the app's requirements, not against a preferred stack, so
  any stack that fits well can score highly. It penalizes needless complexity and stand-ins that
  only appear to work alike, and reads `STACK.md` to credit sound reasoning. The harness weights
  the criteria into a 0-100 score, like the security score.
- **Reporting.** *Stack fit* is a new column in the README, run summaries and cell reports, and a
  metric on the site. The benchmark version is shown next to each run.

### Effect on comparability

Build prompts differ from version 1, so build time, tokens, agent cost, dependencies and the stacks
themselves aren't comparable with earlier runs. The stack fit score exists only from version 2.
Result schema 7 adds `benchmark_version` and `stack_fit`.

## Version 1

The first version, used by every run up to 2026-10-14 #9: five apps built and deployed to Cloudish,
DigitalOcean, Render and Vercel, verified from outside, with an independent security and compliance
review.
