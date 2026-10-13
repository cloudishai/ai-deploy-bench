# Methodology

## The matrix

A run covers every combination of cloud × model × app × trial in [`benchmark.yaml`](../benchmark.yaml),
called a *cell*. Each cloud gets its own reusable-workflow call
([`cloud.yml`](../.github/workflows/cloud.yml)). Each cell gets its own fresh GitHub-hosted runner and
its own Claude Code session, so nothing learned or installed in one cell carries over to another.
Cells of the same cloud run one at a time by default (`max_parallel_per_cloud`). That keeps timings
free of interference from build queues, and avoids clashes over account-wide limits such as
DigitalOcean's single container registry or Render's single free Postgres.

## A cell, step by step

| Step | What happens | Secrets available |
|---|---|---|
| prepare | Creates an empty workspace named after the cell's prefix and copies in `TASK.md` and fixtures. | none |
| build | Claude Code builds the app and tests it locally ([prompt](../bench/templates/build.md)). | model key only |
| deploy | The same Claude Code session resumes and deploys ([prompt](../bench/templates/deploy.md)) and writes `deployment.json`, then the harness times how long the URL takes to answer. | model key, the cloud's prerequisite credentials (none for Cloudish), optional GitHub scratch token |
| inventory | Lists the cloud resources the cell created and prices them, including any created with credentials the agent saved in the workspace's `.env` files. | cloud credentials |
| verify | Waits for the URL to answer, then runs the app's black-box checks. | none |
| teardown | Stops any agent process a cancelled step left behind, deletes what the cell created, then lists again to report leftovers. | cloud credentials |
| finalize | Writes `result.json` and `report.md`, archives the source, and masks secrets in every file. | secrets, only to mask them |

Every cell builds its app from scratch, and the build prompt names the target cloud, so the agent
picks an architecture that suits the platform: serverless functions on one cloud, a container with
a volume on another. That is deliberate: the work and tokens a build takes depend on the
architecture a cloud calls for, so build metrics are part of the comparison. Each cell's report
and the run summary show the stack that was built (frameworks, lines of code, dependencies and
deploy configuration). Because builds also vary from run to run, use `trials` above 1 to tell
platform effects from noise.

The prompts are identical for every cloud except the cloud's name and URL, its credential
variable names, and the cell's resource prefix. Agents get no provider-specific hints, skills or
MCP servers. Finding out how to deploy to each cloud is part of what is measured.

Claude Code runs headless (`claude -p --output-format stream-json`) with `bypassPermissions`, a
pinned version, the model from `benchmark.yaml` and its default effort unless one is configured.
Each phase has a wall-clock limit (`build_timeout_minutes`, `deploy_timeout_minutes`) and a spend
cap (`max_budget_usd_per_phase`, which Claude Code applies per invocation, so a resumed deploy gets
its own budget). The deploy prompt requires every resource name to start with the cell's prefix
(for example `adb-k3x9f-crud`). Agents may set up whatever the cloud lets them set up themselves,
saving any credentials they create in the workspace's `.env`, and must list anything only a person
can do instead of working around it with another provider (see [Human steps](#human-steps)).
Resources are found by the prefix, or because the agent declared them in `deployment.json`.
Declared resources that existed before the cell are priced but never deleted.

When a run is cancelled or a step times out, the harness stops Claude Code and everything it
started before the step ends, so teardown never races a live agent. A cancelled run is not
committed.

## Completion success

A cell is a **success** when its deployment answers on a public HTTPS URL and passes every
*required* check for its app. It is **partial** when it is reachable but at least one required
check fails, and **failed** when there is no reachable deployment. The failure stage is recorded:
`build`, `deploy`, or `human` when the agent couldn't finish without something only a person can
do. Optional checks count toward the cell's **score**, which is checks passed
over checks run. Checks skipped because no browser was available don't count either way.

Every app shares three required checks: the app answers with 2xx within `ready_timeout_minutes`
(which absorbs cold starts and rollouts still in progress), the URL uses HTTPS with a valid
certificate, and it doesn't redirect to another host such as a login wall. Status codes are
checked strictly where the spec names one, with close equivalents accepted (for example 200 or
201 on create, 400 or 422 on validation errors).

| App | Required checks | Optional checks |
|---|---|---|
| [Static site](../apps/static/TASK.md) | `/`, `/about`, `/contact` return HTML with the required headings and form fields (rendered in a browser when the page is client-side); `POST /api/contact` accepts valid input and rejects a bad email or empty message; unknown paths 404; submitting the form in a browser posts to `/api/contact` without a page reload | `<title>` and viewport tags, navigation links, no uncaught JavaScript errors |
| [CRUD app](../apps/crud/TASK.md) | UI served; signup, validation, duplicate email; login and wrong password; tokens required; create, validate, list, rename, complete and delete todos; users can't see or change each other's todos; data still there after a minute with a fresh login | oldest-first order, a login form renders in the browser |
| [API](../apps/api/TASK.md) | health; OpenAPI 3 document; missing or unknown key is 401; create, validate, get, list with tag filter, partial update, delete; notes private per key; data still there after a minute; a burst past 60 requests per minute gets 429, and only for that key | `/docs` page, newest-first order, `Retry-After` header |
| [Dashboard](../apps/dataviz/TASK.md) | dashboard served; `/api/summary` totals, monthly and per-category revenue match values computed independently from the CSV for five filter combinations (including an empty result); a chart renders in the browser | at least two charts, filter controls |
| [Realtime chat](../apps/realtime/TASK.md) | UI served; clients connect (WebSocket or SSE, as declared in `deployment.json`); a message reaches another client within 5 s; rooms stay isolated; five users posting at once all receive every message within 10 s; history endpoint includes recent messages | transport declared, sender echo, over-long messages rejected, UI loads without errors |

The verifiers are tested against reference implementations of all five apps, and against broken
variants to prove each check catches what it should ([`tests/`](../tests)).

## Human steps

The benchmark is about what it takes for an agent to deploy, so the work a person has to do is
measured rather than done quietly in advance. Agents start each cell with only what no agent can
get for itself, the cloud's **prerequisites**, and nothing else is set up for them: no Marketplace
integrations, and no Git hosting unless the optional GitHub scratch account is provided.

| Cloud | Prerequisites (before any agent can deploy) |
|---|---|
| Cloudish | none: agents mint their own API key with one unauthenticated call, with free starter credits |
| DigitalOcean | sign up, add a payment method, create an API token |
| Render | sign up, create an API token |
| Vercel | sign up, create an API token |

Each cell's human steps are collected from evidence by [`bench/human.py`](../bench/human.py):

- **Prerequisites**, from [`benchmark.yaml`](../benchmark.yaml).
- **Help the deployment relies on**: repositories or images in the GitHub scratch account, a
  Marketplace store on Vercel (a person accepted its terms in a browser), or paid resources on a
  cloud whose paid plans need a payment method (`when_paid`).
- **Blockers**: what the agent listed under `human_steps` in `deployment.json`, and provider
  errors in its tool output that only a person can resolve, such as Vercel's
  `integration_terms_acceptance_required`, Render's "You must enter payment information", or
  Cloudish's "API key is out of credits". Blockers count only when the cell didn't succeed: an
  agent that deployed a working app evidently managed without them. A cell that failed or was
  partial and has blockers gets the failure stage `human`.

The **number of distinct steps** is the objective measure. Each step also has an estimated time
from the `human_steps` catalog in `benchmark.yaml`, for someone who already knows what to do
(signing up 3 min, payment method 2, API token 2, accepting integration terms 3, Git hosting 10,
adding credits 3, anything else 5). Replace the estimates with measured times as you get them. Per
cloud, the summary counts each distinct step once across apps, because a person does it once per
account.

## Metrics

| Metric | Definition |
|---|---|
| Build time | Wall-clock time from starting Claude Code for the build phase until its result event. |
| Deploy time | The same, for the deploy phase. Waiting on cloud builds and rollouts is included. |
| Ready after deploy | Extra time between the agent finishing and the app first answering 2xx, probed by the harness right after the deploy phase. It is 0 when the app was already answering. |
| Tokens | Input, output, cache-read and cache-write tokens across all models Claude Code called, per phase. |
| Agent cost | Claude Code's own cost report. It is cumulative over a resumed session, so the deploy phase is the difference between the two phases' totals. It is estimated from token counts and `model_prices` only when a phase ended without a report (timeout or crash), and marked as estimated. |
| Human setup | Distinct human steps the deployment needed or would need, with estimated minutes ([Human steps](#human-steps)). |
| Hosting cost | The estimated monthly cost of the deployed resources (next section), plus the agent's own estimate from `deployment.json` for comparison. |
| Activity | Turns, tool calls by tool, shell commands (with the deploy commands listed in each cell report), tool errors, web searches and fetches, subagents, context compactions. |
| Code | Files, non-blank lines by language, npm and Python dependency counts, frameworks detected, and deploy configuration files (Dockerfile, `vercel.json`, `render.yaml`, `.do/app.yaml`, ...). Dependencies, build output, lockfiles and seeded fixtures are excluded. |
| Performance | p50 and p90 latency of the ready path over 10 requests after the checks, plus WebSocket delivery latency for the chat app. |

## Hosting cost

Each cloud adapter in [`bench/clouds/`](../bench/clouds) lists the resources a cell created and
prices them with the provider's live price APIs where they exist, and otherwise with the dated
tables in [`bench/clouds/pricing/`](../bench/clouds/pricing). The estimate is the cost of keeping
those resources running for a 730-hour month with light traffic:

- **Fixed-price plans** (Render instances and databases, DigitalOcean App Platform instances,
  databases and Droplets) cost their list price per month, times the instance count.
- **Usage-billed compute** (Cloudish containers, billed per second) is priced as always on at the
  provisioned size. Cloudish scales idle apps to zero, so an app with little traffic costs less.
- **Serverless and request-based billing** (Vercel functions, bandwidth, requests) is treated as
  inside the plan's included allowance at benchmark traffic, so it costs $0.
- **Free tiers** cost $0 even when they sleep when idle (Render free web services spin down after
  15 minutes) or expire (Render free Postgres lasts 30 days).
- **Account-level fees** (Vercel Pro seats, Render workspace plans, DigitalOcean registry tiers
  beyond Starter) are not attributed to an app unless the agent created the billed resource.

Resources whose price can't be determined are listed as unpriced, and totals show `+`.

## Fairness and limitations

- **Model knowledge differs by provider.** Long-established CLIs are well covered by training
  data. Newer platforms such as Cloudish have to be discovered from their docs during the run.
  This is part of what the benchmark measures, and it is visible in each cell's web lookups.
- **Human time is estimated.** The steps are collected from evidence, but their minutes come from
  a catalog; first-time setup usually takes longer than the estimates. A person's own model API
  key is not counted, since every cloud needs it equally.
- **Runs are not deterministic.** Use `trials` above 1 to report success rates rather than single
  outcomes.
- **Persistence is checked over a minute.** The checks don't restart the app, so they can't prove
  data survives a redeploy.
- **Leak detection is heuristic.** Resources created during a cell without the prefix are reported
  as possible leaks, but they are not deleted automatically.
- **Credential scoping prevents accidents, not attacks.** Each step gets only the secrets it needs,
  and the agent's environment excludes the runner's file commands (`GITHUB_ENV`, `GITHUB_PATH`, ...)
  and harness variables. But the agent runs as the runner's user with passwordless sudo, so an
  agent determined to misbehave, for example after a prompt injection in a page it fetched, could
  tamper with later steps. Use dedicated cloud accounts with spending limits.
- **Secrets are masked before anything leaves the runner.** That covers the provided values,
  passwords in URLs, and well-known token formats. Transcripts and generated source are uploaded
  as workflow artifacts for 30 days, and only metrics and summaries are committed.
