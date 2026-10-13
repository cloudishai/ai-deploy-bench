{preamble}This is step 2 of 2: deploy the application to {cloud_name} ({cloud_url}).

Make it publicly reachable over HTTPS and make sure every requirement in `TASK.md` works through
the public URL. You can use any {cloud_name} products and tools.

These credentials are set as environment variables:

{credentials}

Use only these credentials: don't sign up for new accounts or create additional API keys or tokens.
Never print secret values, and never write them into files that are committed or deployed.

Rules:

- Name every resource you create (projects, apps, services, databases, repositories, images and so
  on) starting with `{prefix}`, for example `{prefix}-web`.
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
  "notes": "<limitations, manual steps, or anything else a reviewer should know>"
}}
```

Then reply with a short summary of what you deployed and anything that didn't work.
