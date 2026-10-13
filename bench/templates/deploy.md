{preamble}This is step 2 of 2: deploy the application to {cloud_name} ({cloud_url}).

Make it publicly reachable over HTTPS and make sure every requirement in `TASK.md` works through
the public URL. You can use any {cloud_name} products and tools.

{credentials}

Work on your own. If {cloud_name} lets you set up something you need yourself, do it, and save any
credentials you create in `.env` in the current directory, which is never committed or deployed.
If you reach something only a person can do, such as signing up, verifying an email, adding a
payment method, accepting terms in a browser or connecting accounts in a dashboard, don't work
around it with another provider: list it under `human_steps` in `deployment.json` and get as far as
you can without it.

Never print secret values, and never write them into files that are committed or deployed.

Rules:

- Run everything on {cloud_name}{github_clause}. Don't use other hosting services, databases or
  container registries.
- Name every resource you create (projects, apps, services, databases, repositories, images, API
  keys and so on) starting with `{prefix}`, for example `{prefix}-web`.
- Pick the cheapest setup that reliably meets the requirements. Free tiers are fine. Don't buy
  domains or change account plans.
- Before you finish, test the deployed app yourself through its public URL.
{app_notes}
When you're done, write `deployment.json` in the current directory:

```json
{{
  "url": "https://<public base URL of the app>",
  "resources": [
    {{"type": "<for example web service, static site, PostgreSQL database>", "name": "<name>",
     "id": "<provider id, if known>", "plan": "<plan or instance size>", "monthly_cost_usd": 0}}
  ],
  "estimated_monthly_cost_usd": 0,
  "human_steps": [
    {{"step": "<what a person has to do>", "why": "<what it unblocks>", "blocking": true}}
  ],
  "notes": "<limitations, or anything else a reviewer should know>"
}}
```

Leave `human_steps` empty if nothing needed a person. Then reply with a short summary of what you
deployed and anything that didn't work.
