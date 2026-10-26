# Setting up the accounts

The benchmark measures what a person has to do for an agent to deploy (see
[Human steps](methodology.md#human-steps)), so set up only each cloud's **prerequisites** below and
nothing more. Don't pre-install Marketplace integrations or connect Git providers: if an agent
needs them, that is a result, recorded as a human step. Use dedicated accounts, because the harness
deletes anything whose name starts with a cell's prefix and lists every resource created while a
cell was running.

Once the accounts exist, store the keys with [`scripts/set-secrets.sh`](../scripts/set-secrets.sh)
(see [`.env.example`](../.env.example)). The deploy phase first runs with **no credentials at all**,
to measure whether the agent can deploy on its own (see
[Deploying without a human](methodology.md#deploying-without-a-human)); only if that fails does the
agent receive exactly the provided credentials listed for its cloud in
[`benchmark.yaml`](../benchmark.yaml), plus the optional GitHub scratch account. The build phase only
gets the model API key.

| Secret or variable | Kind | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | secret | Claude Code, every cell |
| `DIGITALOCEAN_ACCESS_TOKEN` | secret | DigitalOcean cells |
| `RENDER_API_KEY` | secret | Render cells |
| `VERCEL_TOKEN` | secret | Vercel cells |
| `RAILWAY_API_TOKEN` | secret | Railway cells |
| `BENCH_GITHUB_TOKEN` | secret, optional | All cells, exposed to the agent as `GH_TOKEN` |
| `BENCH_GITHUB_OWNER` | variable, optional | All cells, exposed to the agent as `GH_OWNER` |
| `VERCEL_TEAM_ID` | variable, optional | Vercel cells, when the token can see several teams |
| `RENDER_OWNER_ID` | variable, optional | Render cells, when the key can see several workspaces |

Before any cell starts, the `plan` job lists each planned cloud's resources once with these
credentials (read-only) and fails the run if a token is missing or rejected, so a revoked token
costs nothing. Rerun with the secret updated, or leave that cloud out of `clouds`.

## Anthropic

An API key from the [Claude Console](https://platform.claude.com) with access to every model in
`benchmark.yaml`. Each phase is capped by `max_budget_usd_per_phase` (default $30), and each cell's
security review by `reviewer.max_budget_usd` ($5). Cells for a cloud run one at a time by default,
so expect up to one concurrent session per cloud. The model key
is not counted as a human step, since every cloud needs it equally.

## Cloudish

Nothing to set up. Agents mint their own API key with one unauthenticated call
(`POST /api/v1/keys`), which comes with free starter credits, and save it in the workspace's `.env`.
The harness then inventories, tears down and redacts with that key. If a deployment runs out of
credits, the agent reports it and the cell is blocked on the human step "add credits", which means
claiming the key and adding prepaid credits.

## DigitalOcean

- **Prerequisites:** sign up, add a payment method (accounts need one before they can be used),
  and create a personal access token with read and write scopes (`dop_v1_...`). Custom scopes must
  cover at least apps, databases, droplets, registries, projects, functions, volumes, load
  balancers, Kubernetes and Spaces keys, because the agent may use any of them and teardown has to
  delete them.
- App Platform can't deploy a local folder. It needs a public Git repository (free static sites
  only accept Git sources) or a container image. The token can create a container registry, so
  agents can deploy without Git hosting. Each team has only one registry, which is one reason cells
  for the same cloud run sequentially.
- Teardown can't empty and delete Spaces buckets. Clean those up by hand if an agent creates one.

## Render

- **Prerequisites:** sign up and create an API key (`rnd_...`). Keys can see every workspace you
  belong to; set `RENDER_OWNER_ID` to pin the workspace when there is more than one.
- A payment method is needed only for paid instance types, which fail with
  `402 You must enter payment information` without one. It is counted as a human step whenever a
  deployment uses paid resources.
- Render deploys only from a Git repository or a container image. Without the GitHub scratch
  account, agents have neither, so they will report Git hosting as a blocking human step.
- Free Postgres is limited to one per workspace, which is another reason cells run sequentially.

## Vercel

- **Prerequisites:** sign up and create an access token scoped to the team, or a full-account
  token plus `VERCEL_TEAM_ID`. Hobby works, but it allows one concurrent build and 100 deployments
  a day and is for non-commercial use.
- Databases come from the Vercel Marketplace (Neon, Upstash, ...). The first install on a team
  needs a person to accept the integration's terms in a browser. Don't do it in advance: agents
  that need a database report it, and the CLI's `integration_terms_acceptance_required` response is
  detected. If you install an integration anyway, every deployment that uses it is charged that
  human step.
- A payment method is counted when a deployment uses paid resources.
- CLI-created projects default to Vercel Authentication on deployment URLs; only the production
  domain is public. The verifier fails deployments whose URL redirects to a login page.

## Railway

- **Prerequisites:** sign up at [railway.com](https://railway.com) and create an **account or
  workspace** API token (Account Settings → Tokens). A project-scoped token can only deploy to an
  existing project, so it can't be used here. Set it as `RAILWAY_API_TOKEN`. A workspace token
  can't read the account (`me`), so the harness lists that workspace's projects instead. Sign up
  with GitHub to avoid the Limited Trial, which restricts outbound network access.
- `railway up` uploads the local folder and builds it on Railway, so **no Git hosting is needed** —
  agents don't need the GitHub scratch account.
- The free trial ($5 of credit for 30 days, no card) covers a benchmark deployment, but it caps a
  workspace at **2 projects** — `projectCreate` then fails with "Free plan resource provision limit
  exceeded". Each cell creates one project and teardown deletes it, so a clean sequential run stays
  under the cap; but leftover projects (from a failed teardown, or other work in the same workspace)
  will exhaust it and block later cells on a `payment_method` human step. Use a dedicated workspace,
  and add a payment method / Hobby plan to remove the cap for a full run.
- Railway bills actual usage per second, so hosting costs are estimated from an assumed per-service
  size (see [`bench/clouds/pricing/railway.yaml`](../bench/clouds/pricing/railway.yaml)). Teardown
  deletes each project the cell created (named with the cell prefix), which removes its services and
  volumes.

## GitHub scratch account (optional)

Providing Git hosting is itself a human step (about 10 minutes in the catalog), counted for every
deployment that uses it. Leave it unset to measure what agents do without it; set it to measure
Git-based deploys on Render and DigitalOcean.

Use a dedicated GitHub organization or user (for example `yourname-bench`) where agents may create
repositories and push container images, named with the cell prefix and deleted at teardown. Create
a classic personal access token with the `repo`, `delete_repo`, `write:packages` and
`delete:packages` scopes (fine-grained tokens can't use GitHub Packages), then set
`BENCH_GITHUB_TOKEN` and `BENCH_GITHUB_OWNER`. The token must belong to that user, or have admin
rights on that organization. Never use an account that holds anything you care about.

Agents often make these repositories public, because DigitalOcean and Render deploy public
repositories without connecting an app. The prompt forbids committing credentials, and GitHub's
secret scanning push protection (on by default for public repositories) blocks pushes that
contain known token formats. Keep it enabled on the scratch account.

## This repository

- **Results as a pull request:** the collect job opens a PR with `results/` and `README.md` rather
  than committing to the default branch, so a person reviews each run first (a run can include cells
  that failed for reasons only a person can judge, such as a missing payment method). Enable
  **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests** so
  `GITHUB_TOKEN` can open it. To skip the PR and only keep the artifacts, run with
  `open_results_pr: false`.
- **Runner minutes:** each cell is one job of up to about 3 hours, mostly waiting on the agent and
  the cloud. A full run is 20 cells.
- **Leftovers:** if a teardown fails, run the *Cleanup* workflow. It lists `adb-*` resources older
  than 6 hours and deletes them when `delete` is checked. Agents' Cloudish keys aren't swept, but
  each one only holds its free starter credits.
