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
| deploy | The same Claude Code session resumes and deploys ([prompt](../bench/templates/deploy.md)), writing `deployment.json`; the harness times how long the URL takes to answer. Runs up to twice: first with **no credentials at all**, then — only if that didn't produce a working public URL — again with the cloud's credentials (see [Deploying without a human](#deploying-without-a-human)). | first attempt: model key only; second attempt: model key, the cloud's prerequisite credentials (none for Cloudish), optional GitHub scratch token |
| inventory | Lists the cloud resources the cell created and prices them, including any created with credentials the agent saved in the workspace's `.env` files. | cloud credentials |
| verify | Waits for the URL to answer, then runs the app's black-box checks. | none |
| review | A separate Claude Code session reviews the security and compliance of the process, the code, the hosting plan and the live app, and rates the stack the agent chose ([prompt](../bench/templates/review.md)). | model key only |
| teardown | Stops any agent process a cancelled step left behind, deletes what the cell created, then lists again to report leftovers. | cloud credentials |
| finalize | Writes `result.json` and `report.md`, archives the source, and masks secrets in every file. | secrets, only to mask them |

Every cell builds its app from scratch, and the build prompt names the target cloud, so the agent
picks an architecture that suits the platform: serverless functions on one cloud, a container with
a volume on another. Before writing code, it compares the two or three most plausible stacks for
the app and records them and its choice in `STACK.md`; the prompt states there is no default
language or framework, and suggests no technology for any app (from benchmark version 2, see
[CHANGES.md](../CHANGES.md)). That is deliberate: the work and tokens a build takes depend on the
architecture a cloud calls for, so build metrics are part of the comparison. Each cell's report
and the run summary show the stack that was built (frameworks, lines of code, dependencies and
deploy configuration). Because builds also vary from run to run, use `trials` above 1 to tell
platform effects from noise.

The prompts are identical for every cloud except the cloud's name and URL, its credential
variable names, and the cell's resource prefix. Agents get no provider-specific hints, skills or
MCP servers. Finding out how to deploy to each cloud is part of what is measured.

Claude Code runs headless (`claude -p --output-format stream-json`) with `bypassPermissions`, a
pinned version, and the model and effort from `benchmark.yaml`. A model marked `hipaa: true` uses an
API key from an organization with the HIPAA configuration, which rejects Claude Code's advisor tool
and pre-release API features, so those are turned off for it; reports note it next to the model.
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

## Rerunning part of a run

When a harness bug only affected some cells, say one cloud's inventory or teardown, those cells
can be rerun on their own and merged with the full run they belong to, instead of rerunning
everything. Run the benchmark with `base_run` set to that run's name and the cells to rerun chosen
as usual (for example `clouds: railway`). The new run's own cells replace the base run's, and every
other cell is copied from the base run unchanged: its record, report and screenshots. The new run
then covers the whole matrix, so it is a full run and updates the README.

Cells are independent (a fresh runner and Claude Code session each), so a copied cell is exactly
what a full rerun would have kept, provided the fix doesn't touch it. That is for whoever reruns to
judge. A fix to anything every cell shares, such as the prompts, the verifiers or a rubric, needs a
full run, and usually a new benchmark version. The harness refuses a base run that:

- isn't a full run,
- ran a different benchmark version, Claude Code version or set of models, or
- is more than 7 days older than the rerun, since clouds change their products and prices.

It checks this when planning, before any cell runs. A merged run records its base (`base_run`) and
what was rerun (`rerun`), each copied cell records the run that produced it (`from_run`), and the
summaries and the site say so. Trends on the site skip a cloud whose cells were all copied, so the
base run's results aren't plotted twice. Times and costs of copied cells are the base run's.

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

### Screenshots

While the deployment is live, the verifier also takes screenshots in its browser so people can see
what each agent built. They don't affect any score.

| App | Screenshots |
|---|---|
| Static site | The home page, and the contact page after the verifier submitted the form |
| CRUD app | The app before signing in, and the todo list after signing in through the web UI as the verifier's test user. The second is kept only when the page shows that user's todos, so a UI the verifier can't drive leaves no misleading picture |
| API | The `/docs` page |
| Dashboard | The dashboard once its charts render, or after 30 seconds |
| Realtime chat | The room the verifier's clients chatted in, which shows its history if the UI does |

Each is a 1280×900 JPEG, shown in the cell's report and, for the first trial, in the run summary's
gallery. Pixels can't be masked like text, so the verifier saves each page's text next to its
screenshot, and finalize deletes any screenshot whose page showed a secret or that has no text.

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
| Railway | sign up, create an account or workspace API token |

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

## Deploying without a human

Human steps measure how much a person has to do; this measures the sharper question of whether the
cloud needs a person at all. Every cell's deploy phase first runs with **no credentials provided** —
no cloud token and no GitHub scratch account. The agent gets the same deploy prompt, which tells it
to set up whatever it can on its own and to list anything only a person could do under `human_steps`.

- If that no-credentials attempt produces a publicly answering URL and the agent reports no blocking
  human step, it is kept as the cell's deployment, and the cell counts as **deployed without a
  human**.
- Otherwise the cloud's credentials are provided and the same Claude Code session reruns. That keyed
  attempt is the cell's result, measured exactly as deploys were before this was added.

The summary's **Deploys without human** column is, per cloud, the number of apps deployed with no
credentials out of the apps attempted. Cloudish scores here because its agents mint their own key;
clouds that need a browser signup and a dashboard token do not. The no-credentials attempt's time,
tokens and cost are added to the cell's totals and also recorded on their own (`no_human`,
`cost.agent_nohuman_deploy_usd`, `tokens.deploy_nohuman`, `timing.deploy_nohuman_s`), so the extra
spend is visible rather than hidden.

## Security and compliance review

After verification, while the deployment is still live, a separate Claude Code session reviews how
securely the app was built and deployed, whether its hosting fits how the app will be used, and what
is running. The reviewer is the same for every cell
(`reviewer` in `benchmark.yaml`: Opus 5.5 at high effort), whatever model built the app, and it gets
the model key only, never cloud credentials. It works from:

- a copy of the code and configuration the agent produced, with secrets masked;
- condensed transcripts of the build and deploy sessions: the agent's messages, every command and
  tool call, and abbreviated results. A masked value in a command shows that a secret appeared there;
- `deployment.json` and the resources the benchmark found;
- how the app will be used (`use` in `benchmark.yaml`: `commercial` for the landing page, the team
  todo list and the sales dashboard, `personal` for the notes API and the club chat) and what the
  benchmark could read about the cloud account, such as Vercel's team plan;
- the live URL, which it may probe like a careful outside tester, sending at most 100 requests and
  no brute-forcing, fuzzing or load.

It scores each criterion of `security_rubric` from 0 to 10, with evidence for every finding. The
harness computes the 0–100 score from the criterion weights, so the arithmetic isn't left to the
model:

| Criterion | Weight | Question |
|---|---|---|
| Secrets handling | 25 | Were credentials kept out of logs, code, build contexts and deployed files, and read from the platform's secret mechanism? |
| Deployment provenance | 20 | Is what runs the code that was built, deployed from sources the owner controls, with trusted, pinned build inputs? |
| Terms compliance | 15 | Does the hosting fit the app's use and the provider's terms: no non-commercial plan for a business's app, no reliance on a free tier that expires or sleeps where the app must stay up? |
| Least privilege | 15 | Private data stores, non-root containers, minimal permissions and access modes? |
| Transport security | 10 | HTTPS only with a valid certificate; missing security headers are minor unless the platform could have set them? |
| Attack surface | 10 | Nothing exposed beyond the app: no source, `.env` or `.git`, directory listings, debug endpoints or stack traces? |
| Application security | 5 | Input validation, correct authentication and authorization, no injection or XSS, public endpoints protected against abuse? |

The weights favor how the app was deployed over the app's own code. The code would have the same
weaknesses on any cloud, so it says little about the cloud; it is still reviewed, but counts for 5.

## Stack fit

From benchmark version 2, the same review session also rates the stack the agent chose for the app:
its language, frameworks, libraries, data stores and hosting. It judges the stack against the app's
requirements in `TASK.md`, not against a stack it would have preferred, so any stack that fits well
can score highly, including an unexpected one. When the agent recorded its decision in `STACK.md`,
the reviewer credits sound reasoning and notes where the build departed from it. Each criterion of
`stack_rubric` is scored from 0 to 10 and weighted by the harness into a separate 0–100 score:

| Criterion | Weight | Question |
|---|---|---|
| Fit for the job | 40 | Does each part suit its job: a durable store for persistent data, a suitable transport for realtime, static hosting for static content? |
| Proportion | 30 | Is it as simple as the requirements allow, with no needless services, frameworks or dependencies, and no stand-ins that only appear to work, such as a blob store used as a database? |
| Platform fit | 30 | Does it use what the cloud does well, or work against it? |

The stack fit score is reported next to the security score but kept separate from it, and from
success: a stack that fits poorly can still pass every check. A missing or invalid stack rating
doesn't invalidate the security review.

Cells without a reachable deployment aren't reviewed. The reviewer's cost is reported separately and
isn't added to the agent cost. Each cell's report lists the criterion scores, the rationale and the
findings, and the summaries average the score per cloud. Each finding names its source, the party
that would have to fix it: the `platform` (the cloud's own behavior or defaults), the `deployment`
(how the agent built and deployed) or the `app` (the code the agent wrote).

## Metrics

| Metric | Definition |
|---|---|
| Build time | Wall-clock time from starting Claude Code for the build phase until its result event. |
| Deploy time | The same, for the deploy phase. Waiting on cloud builds and rollouts is included. |
| Ready after deploy | Extra time between the agent finishing and the app first answering 2xx, probed by the harness right after the deploy phase. It is 0 when the app was already answering. |
| Tokens | Input, output, cache-read and cache-write tokens across all models Claude Code called, per phase. |
| Agent cost | Claude Code's own cost report. It is cumulative over a resumed session, so the deploy phase is the difference between the two phases' totals. It is estimated from token counts and `model_prices` only when a phase ended without a report (timeout or crash), and marked as estimated. |
| Human steps | Distinct human steps the deployment needed or would need ([Human steps](#human-steps)). |
| Human time | Estimated minutes for those steps, from the `human_steps` catalog. |
| Deploys without human | Apps the agent deployed with no credentials provided, out of those attempted ([Deploying without a human](#deploying-without-a-human)). |
| Security & compliance | 0–100 score from the independent review ([Security and compliance review](#security-and-compliance-review)). |
| Stack fit | 0–100 rating of the stack the agent chose, from the same review ([Stack fit](#stack-fit)). From benchmark version 2. |
| Hosting cost | The estimated monthly cost of the deployed resources with light use and when busy ([Hosting cost](#hosting-cost)), plus the agent's own estimate from `deployment.json` for comparison. |
| Activity | Turns, tool calls by tool, shell commands (with the deploy commands listed in each cell report), tool errors, web searches and fetches, subagents, context compactions. |
| Code | Files, non-blank lines by language, npm and Python dependency counts, frameworks detected, and deploy configuration files (Dockerfile, `vercel.json`, `render.yaml`, `.do/app.yaml`, ...). Dependencies, build output, lockfiles and seeded fixtures are excluded. |
| Technologies | What the app was built and run with, by group: runtime, frameworks, data stores, libraries, dev tools, packaging and hosting. [`bench/stack.py`](../bench/stack.py) names them from facts the harness records about the workspace (declared packages, Dockerfile base images, requested runtime versions, built-in modules such as `node:http` and `node:sqlite`) and from the cloud resources the inventory found. Records keep the facts, so a better catalog describes earlier runs better too. |
| Performance | p50 and p90 latency of the ready path over 10 requests after the checks, plus WebSocket delivery latency for the chat app. |

## Hosting cost

Clouds bill in different ways: some charge a fixed price per instance, some per second while a
container runs, and some per request with free allowances. A single "monthly cost" therefore only
compares fairly at a stated level of traffic. Each deployment is priced for a month at two levels,
defined in `hosting_usage` in `benchmark.yaml`:

| | Light use | Busy |
|---|---|---|
| Who uses it | A few visits a week | A public app that crawlers, uptime monitors and visitors hit around the clock |
| Requests a month | 2,000 | 2,628,000 (one a second) |
| Hours a scale-to-zero app is awake | 10 (idle timeouts included) | 730 (it never goes idle) |
| Outbound transfer (20 KB a request) | 0.04 GB | 52.6 GB |
| Requests that reach app code | half, at 20 ms of CPU and 100 ms with 2 GB of memory each | the same |

Each cloud adapter in [`bench/clouds/`](../bench/clouds) lists the resources a cell created,
gives each its list price at the size it was provisioned, from the provider's live price API
where there is one and otherwise from the dated tables in
[`bench/clouds/pricing/`](../bench/clouds/pricing), and then prices the whole deployment at each
level:

- **Cloudish** bills containers per second while they run and scales idle ones to zero after 15
  minutes, so a container costs its size's hourly rate for the hours it is awake: 10 at light use,
  730 when busy. Cloudish lists no bandwidth or request charges.
- **DigitalOcean App Platform** containers always run, so they cost their fixed price at both
  levels. Each container size includes outbound transfer (50 GiB a month for the $5 size), pooled
  across the team's apps, and beyond it transfer costs $0.02 per GiB. Static-only apps get 1 GiB.
- **Render** paid instances cost their plan price at both levels. Free web services cost nothing
  while the workspace's 750 free instance hours last, and spin down after 15 idle minutes. Outbound
  transfer beyond the workspace plan's allowance costs $0.15 per GB. The API doesn't report the
  workspace plan, so the benchmark assumes Hobby, which includes 5 GB. Without a payment method on
  file, Render suspends the services instead of billing the extra transfer.
- **Vercel** Hobby is free within fixed monthly limits (1M CDN requests, 100 GB of transfer, 1M
  function invocations, 4 hours of active CPU, 360 GB-hours of memory). It pauses projects that
  exceed them, can't buy more, and is for personal, non-commercial use only. So on a Hobby team, a
  business's app (`use: commercial` in `benchmark.yaml`), or traffic beyond the limits, is priced
  on Pro: the $20 monthly platform fee, which includes $20 of usage credit, plus usage beyond the
  credit at Pro's on-demand rates. On a Pro team, only usage beyond the credit counts, since the
  fee is paid once per team.
- **Databases, volumes, registries and other fixed-price resources** cost their list price at both
  levels.
- **Free tiers** cost $0 even when they sleep when idle or expire (Render free Postgres lasts 30
  days). The security and compliance review judges whether relying on them suits the app.
- **Other account-level fees** (Render workspace plans, Vercel seats beyond the first) aren't
  attributed to an app.

The two levels bracket what a small app costs: light use shows what scale-to-zero and free plans
save when nobody visits, and busy shows what an app costs once it never idles. Each cell report
explains how each figure was reached. Resources whose price can't be determined are listed as
unpriced, and totals show `+`. Each resource's list price, always on at its provisioned size, is
also recorded (`hosting_monthly_usd`).

## Result files

Everything under `results/` is plain JSON and markdown, so other tools, such as a results website,
can read it directly. Paths inside the JSON files are relative to the folder given in the table.

| File | Contents |
|---|---|
| `results/index.json` | `runs`: every run, newest first, with its name, date, scope, models, cell and success counts, and the paths of its `summary` (JSON) and `report` (markdown), relative to `results/` |
| `results/runs/<run>/summary.json` | `run` (metadata), `groups` (one row per model × cloud) and `cells` (one compact row per cell, with the `path` of its full record and its `report`, relative to the run folder) |
| `results/runs/<run>/cells/<model>/<cloud>/<app>-t<trial>.json` | The cell's full record: outcome, checks, timing, tokens and cost per phase, human steps, resources, code statistics, the security review (`security.criteria`, `security.findings`, `security.summary`) and `screenshots` (`name`, `caption`, `url`, and `file` relative to the record's folder, or `error` when one wasn't captured or was removed) |
| `results/runs/<run>/cells/<model>/<cloud>/<app>-t<trial>/<name>.jpg` | The cell's screenshots |

Every file has a `schema` number, raised whenever fields are added, renamed or removed. Files from
earlier runs keep the schema they were written with, so readers should treat fields added in later
versions as optional:

| Schema | Changes |
|---|---|
| 1 | First version. Runs before the security review have no `security` block |
| 2 | `results/index.json`; `schema` in `summary.json`; `path` and `report` on summary cells; `source` on security findings |
| 3 | The review adds a `compliance` criterion and reweights the rubric (shown as *Security & compliance*), so scores aren't comparable with earlier runs. The JSON fields keep their names (`security`, `security_score`) |
| 4 | `cost.hosting_usage` in cell records (cost, `incomplete` and `basis` for each traffic level), and `hosting_usage_usd` and `hosting_usage_incomplete` on summary cells and groups |
| 5 | `screenshots` in cell records, and their file names on summary cells |
| 6 | `technologies` in cell records (names by group) and on summary cells (a short headline), and the facts they come from in `code`: `packages`, `base_images`, `runtime_hints`, `builtins`, `manifests` and `dirs`. These fields were also added to the records of runs 2026-10-13 #4, #5 and #8, from their source snapshots; nothing else in those records changed |
| 7 | `benchmark_version` in cell records, in `run` in `summary.json` and in `results/index.json`; `stack_fit` in cell records (`status`, `score`, `criteria`, `summary`), and `stack_fit_score` on summary cells and groups |
| 8 | `deploys_without_human` and `no_human` in cell records, with the no-credentials attempt's `cost.agent_nohuman_deploy_usd`, `tokens.deploy_nohuman` and `timing.deploy_nohuman_s`; `deploys_without_human` on summary cells and groups |
| 9 | Merged runs ([rerunning part of a run](#rerunning-part-of-a-run)): `base_run` and `rerun` in `run` in `summary.json` and in `results/index.json`, and `from_run` (`name`, `date`, `number`, `attempt`, `url`, or null) on summary cells |

## Fairness and limitations

- **Model knowledge differs by provider.** Long-established CLIs are well covered by training
  data. Newer platforms such as Cloudish have to be discovered from their docs during the run.
  This is part of what the benchmark measures, and it is visible in each cell's web lookups.
- **The security and compliance score is a model's judgment.** A fixed rubric, required evidence and
  the same reviewer for every cell keep it comparable, but reviews vary from run to run like the
  deployments do. The reviewer also can't inspect cloud settings it has no credentials for, and it
  judges providers' terms from what it knows of them.
- **The stack fit score is a model's judgment too,** and the reviewer is the same model family as
  the agent, so it may favor the stacks that family tends to choose. The rationale for each
  criterion is published so the scores can be checked.
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
