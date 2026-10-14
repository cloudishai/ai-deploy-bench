# Website

The benchmark's site, [aideploybench.com](https://aideploybench.com): a static site generated from
[`results/`](../results) and served from [Cloudish](https://cloudish.ai). It has a page for every
run and every cell (checks, security review, human steps, costs, what the agent built, its deploy
summary and screenshots of the live app), and trend charts of each metric over runs, one line per
cloud: across all apps for full runs, and per app for every run that included it.

## Build and preview

```bash
pip install -r requirements.txt -r website/requirements.txt
python -m website.build                                   # writes website/dist
python -m http.server 8000 --directory website/dist       # http://localhost:8000
```

Pages are rendered with Jinja2 (`templates/`), charts are SVG drawn at build time (`charts.py`), and
the only script is the chart legends' toggle (`static/app.js`). Nothing is loaded from other hosts,
and pages have no inline scripts or styles, so `nginx.conf` can send a strict Content-Security-Policy.
Runs from older versions of the benchmark have older result schemas; `data.py` treats every field
added since the first one as optional. `tests/test_website.py` builds the site from the committed
results and checks that every internal link resolves.

## Deploy

[`.github/workflows/website.yml`](../.github/workflows/website.yml) builds and deploys on every push
to `main` that changes the results, the site or the docs, and after every benchmark run (its results
commit is made with `GITHUB_TOKEN`, which doesn't trigger push workflows). `python -m website.deploy`:

1. uploads `Dockerfile`, `nginx.conf` and `dist/` to Cloudish, which builds the image (non-root
   nginx, pinned by digest) and runs it as the project `ai-deploy-bench/aideploybench`;
2. keeps the subdomain [aideploybench.on.do.cloudish.ai](https://aideploybench.on.do.cloudish.ai)
   and the custom domains `aideploybench.com` and `www.aideploybench.com` (which redirects to the
   first) configured;
3. waits until the site serves the new build, from the commit in its `<meta name="build">` tag.

It needs the repository secret `WEBSITE_CLOUDISH_API_KEY`, a Cloudish key with credits:

```bash
gh secret set WEBSITE_CLOUDISH_API_KEY   # paste the key; it's read from stdin, not the command line
```

The container scales to zero when idle and costs its hourly rate while awake, plus 0.01 credits a
day per active domain. Check the balance at [cloudish.ai](https://www.cloudish.ai).

## DNS

Each domain needs its verification TXT record (once), and a record pointing at `do.cloudish.ai`.
The deploy log prints the TXT values for domains that aren't active yet.

| Type | Name | Value |
|---|---|---|
| TXT | `_cloudish-challenge.aideploybench.com` | `cloudish-verify=…` (from the deploy log) |
| TXT | `_cloudish-challenge.www.aideploybench.com` | `cloudish-verify=…` (from the deploy log) |
| A | `aideploybench.com` | the address of `do.cloudish.ai` (`dig +short do.cloudish.ai`), or an ALIAS/flattened CNAME to it |
| CNAME | `www.aideploybench.com` | `do.cloudish.ai` |

Cloudish checks the TXT records every minute and issues certificates once both records of a domain
are in place.
