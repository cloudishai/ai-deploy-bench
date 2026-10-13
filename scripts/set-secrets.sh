#!/usr/bin/env bash
# Stores the benchmark's API keys as GitHub Actions secrets, and account-scoping IDs as variables.
#
#   cp .env.example .env   # fill it in; .env is gitignored
#   scripts/set-secrets.sh [owner/repo]
#
# Values are read from the file without executing it and are passed to gh on stdin, so they never
# appear in the process list or shell history. Empty values are skipped, never cleared.
set -euo pipefail

repo="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
env_file="${ENV_FILE:-.env}"
# No Cloudish key: agents mint their own, and a pre-made one would hide that from the benchmark.
secrets="ANTHROPIC_API_KEY DIGITALOCEAN_ACCESS_TOKEN RENDER_API_KEY VERCEL_TOKEN BENCH_GITHUB_TOKEN"
variables="BENCH_GITHUB_OWNER VERCEL_TEAM_ID RENDER_OWNER_ID"

if [ ! -f "$env_file" ]; then
  echo "error: $env_file not found; copy .env.example to .env and fill it in" >&2
  exit 1
fi

# Prints the value assigned to $1 in the env file, without surrounding whitespace or quotes.
value_of() {
  local line
  line=$(grep -E "^[[:space:]]*$1[[:space:]]*=" "$env_file" | tail -n 1) || return 0
  line="${line#*=}"
  line="${line%$'\r'}"
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  case "$line" in
    \"*\" | \'*\') line="${line:1:${#line}-2}" ;;
  esac
  printf '%s' "$line"
}

echo "Configuring $repo from $env_file"
for name in $secrets; do
  value=$(value_of "$name")
  if [ -n "$value" ]; then
    printf '%s' "$value" | gh secret set "$name" --repo "$repo"
    echo "  secret    $name: set"
  else
    echo "  secret    $name: skipped (empty)"
  fi
done
for name in $variables; do
  value=$(value_of "$name")
  if [ -n "$value" ]; then
    gh variable set "$name" --repo "$repo" --body "$value" >/dev/null
    echo "  variable  $name: set"
  else
    echo "  variable  $name: skipped (empty)"
  fi
done
