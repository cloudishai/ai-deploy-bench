# Setting up the accounts

The benchmark runs against real accounts. Use dedicated ones: the harness deletes anything whose
name starts with a cell's prefix, and its leak detection lists every resource created while a cell
was running. Once everything below exists, store the keys with
[`scripts/set-secrets.sh`](../scripts/set-secrets.sh) (see [`.env.example`](../.env.example)).

What the agent receives during the deploy phase is exactly the environment variables listed for
its cloud in [`benchmark.yaml`](../benchmark.yaml), plus the optional GitHub scratch account. The
build phase only gets the model API key.

| Secret or variable | Kind | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | secret | Claude Code, every cell |
| `CLOUDISH_API_KEY` | secret | Cloudish cells |
| `DIGITALOCEAN_ACCESS_TOKEN` | secret | DigitalOcean cells |
| `RENDER_API_KEY` | secret | Render cells |
| `VERCEL_TOKEN` | secret | Vercel cells |
| `BENCH_GITHUB_TOKEN` | secret, optional | All cells, exposed to the agent as `GH_TOKEN` |
| `BENCH_GITHUB_OWNER` | variable, optional | All cells, exposed to the agent as `GH_OWNER` |
| `VERCEL_TEAM_ID` | variable, optional | Vercel cells, when the token can see several teams |
| `RENDER_OWNER_ID` | variable, optional | Render cells, when the key can see several workspaces |

## Anthropic

An API key from the [Claude Console](https://platform.claude.com) with access to every model in
`benchmark.yaml`. Each phase is capped by `max_budget_usd_per_phase` (default $30). Cells for a
cloud run one at a time by default, so expect up to one concurrent session per cloud.

## Cloudish

A Cloudish API key with prepaid credits. Mint one with `curl -X POST https://cloudish.ai/api/v1/keys`,
then claim it and add credits through `GET /api/v1/credits/claim`
(see [credits.md](https://cloudish.ai/credits.md)). Builds cost about a cent each, and containers
are billed per second only until teardown.

Cloudish's docs tell agents to mint their own key per project folder. The prompt forbids that, but
if an agent does it anyway and saves the key in the workspace's `.env`, the harness inventories,
tears down and redacts with that key too. Agents can also change key-level settings such as the
idle timeout (`PATCH /api/v1/me`), which persist across cells. Check them between runs.

## DigitalOcean

- A dedicated team with a payment method.
- A personal access token with read and write scopes (`dop_v1_...`). Custom scopes must cover at
  least apps, databases, droplets, registries, projects, functions, volumes, load balancers,
  Kubernetes and Spaces keys, because the agent may use any of them and teardown has to delete them.
- App Platform can't deploy a local folder. It needs a public Git repository (free static sites
  only accept Git sources) or a container image (DigitalOcean Container Registry, Docker Hub or
  GHCR). The token can create a registry, but each team has only one, which is one reason cells
  for the same cloud run sequentially.
- Teardown can't empty and delete Spaces buckets. Clean those up by hand if an agent creates one.

## Render

- A dedicated workspace with a payment method. Without one, paid instance types fail with
  `402 You must enter payment information`, and Render defaults to a paid instance when no plan
  is given.
- An API key (`rnd_...`). Keys can see every workspace you belong to; set `RENDER_OWNER_ID` to
  pin the workspace when there is more than one.
- Render deploys only from a Git repository or a container image, so configure the GitHub scratch
  account below. Public repositories deploy without connecting Render's GitHub app. For private
  ones, install the Render GitHub app on the scratch account with access to all repositories.
- Free Postgres is limited to one per workspace, which is another reason cells run sequentially.

## Vercel

- A dedicated team. Hobby works, but it allows one concurrent build and 100 deployments a day and
  is for non-commercial use. Pro removes those limits.
- An access token scoped to that team, or a full-account token plus `VERCEL_TEAM_ID`.
- Databases come from the Vercel Marketplace (Neon, Upstash, ...). Installing an integration the
  first time needs a human to accept its terms in the browser, which an agent cannot do. Install
  Neon and Upstash on the team once before running the CRUD, API and realtime apps.
- CLI-created projects default to Vercel Authentication on deployment URLs; only the production
  domain is public. The verifier fails deployments whose URL redirects to a login page.

## GitHub scratch account (optional, recommended)

A dedicated GitHub organization or user (for example `yourname-bench`) where agents may create
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

- **Workflow permissions**: the collect job pushes results with `GITHUB_TOKEN` and
  `contents: write`. If `main` is protected, allow GitHub Actions to push or run without committing
  (`commit_results: false`) and download the artifacts instead.
- **Runner minutes**: each cell is one job of up to about 3 hours, mostly waiting on the agent and
  the cloud. A full run is 20 cells.
- **Leftovers**: if a teardown fails, run the *Cleanup* workflow. It lists `adb-*` resources older
  than 6 hours and deletes them when `delete` is checked.
