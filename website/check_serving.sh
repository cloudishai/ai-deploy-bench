#!/usr/bin/env bash
# Builds the site's image from website/dist and checks how nginx serves it: pages, their markdown
# versions (by URL and by `Accept: text/markdown`), llms.txt, robots.txt and the security headers.
# Run from the repository root after `python -m website.build`; needs Docker.
set -euo pipefail

docker build --quiet --tag aideploybench-check website >/dev/null
id=$(docker run --detach --publish 8080:8080 aideploybench-check)
trap 'docker rm --force "$id" >/dev/null' EXIT
until curl --silent --fail http://localhost:8080/healthz >/dev/null; do sleep 0.5; done

failed=0
check() {  # check <description> <expected substring> <curl args...>
  local what=$1 expected=$2; shift 2
  local got; got=$(curl --silent --include "$@")
  if grep --quiet --ignore-case --fixed-strings -- "$expected" <<<"$got"; then echo "ok   $what"
  else echo "FAIL $what: expected '$expected'"; head -20 <<<"$got"; failed=1; fi
}
base=http://localhost:8080
check "home is HTML" "content-type: text/html" "$base/"
check "home has a strict CSP" "content-security-policy: default-src 'self'" "$base/"
check "pages vary by Accept" "vary: Accept" "$base/"
check "home links its markdown" 'rel="alternate" type="text/markdown" href="/index.md"' "$base/"
check "markdown by URL" "content-type: text/markdown; charset=utf-8" "$base/index.md"
check "markdown by Accept" "# AI Deploy Bench" -H "Accept: text/markdown" "$base/"
check "markdown by Accept, nested page" "content-type: text/markdown" -H "Accept: text/markdown" "$base/clouds/railway/"
check "markdown by Accept, no trailing slash" "# Railway" -H "Accept: text/markdown" "$base/clouds/railway"
check "browsers still get HTML" "content-type: text/html" -H "Accept: text/html,application/xhtml+xml,*/*;q=0.8" "$base/clouds/railway/"
check "llms.txt" "content-type: text/plain; charset=utf-8" "$base/llms.txt"
check "llms-full.txt" "# AI Deploy Bench" "$base/llms-full.txt"
check "robots.txt points at the sitemap" "Sitemap: https://aideploybench.com/sitemap.xml" "$base/robots.txt"
check "sitemap" "<lastmod>" "$base/sitemap.xml"
check "data index" "content-type: application/json" "$base/data/index.json"
check "missing pages are 404" "HTTP/1.1 404" "$base/no-such-page/"
exit $failed
