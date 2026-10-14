# Railway: can an agent set up without a human?

Working log for adding [Railway](https://railway.com) as a cloud (issue follow-up). The question:
does an agent need a human to create an account and token (like DigitalOcean/Render/Vercel), or can
it bootstrap itself with no human steps (like Cloudish)? Everything tried is recorded here so the
benchmark can state honestly what Railway needs.

Date: 2026-10-14. Attempts run from a clean machine with no Railway account and no token.

## What the docs say

- **Public API** (`https://backboard.railway.com/graphql/v2`) authenticates with account, workspace
  or project tokens, all created by hand on dashboard pages; OAuth needs a human to approve. No
  documented way to mint a token programmatically.
- **CLI** `railway up` uploads a local folder (no Git hosting needed), but authenticates with
  `RAILWAY_API_TOKEN` (account/workspace) or `RAILWAY_TOKEN` (project); `railway login` needs a
  browser. Project tokens can only deploy to an existing environment, not create projects.
- **Account-free deploys** ("Railway for Everyone", Aug 2026) are browser-only (railway.com/new,
  dev.new), limited to sites and databases, hidden behind Edge Rules so only the creator sees them,
  and cleaned up after 24h unless claimed. No CLI/API path. Not usable for the benchmark (needs a
  public URL).
- **`ssh railway.new`**: first connection from a new machine "returns a link to sign up or sign in
  and approve your SSH key" — still a human.

Conclusion from docs: looks like a human is needed (signup + token), same shape as Render/Vercel.

## Attempts

### 1. Public API with no token

```
curl https://backboard.railway.com/graphql/v2 -H 'Content-Type: application/json' \
  -d '{"query":"query { me { id email } }"}'
# -> 200  {"errors":[{"message":"Not Authorized",...}],"data":null}
```

`me` is rejected without a token, as expected.

### 2. projectCreate with no token — unexpectedly succeeded

```
curl https://backboard.railway.com/graphql/v2 -H 'Content-Type: application/json' \
  -d '{"query":"mutation { projectCreate(input: {name: \"adb-probe\"}) { id } }"}'
# -> 200  {"data":{"projectCreate":{"id":"23658738-d8bd-4e34-a4e6-e72881f441a7"}}}
```

An unauthenticated `projectCreate` returned a project id. This is surprising and worth
understanding before relying on it: a project with no owner may be an anonymous/ephemeral project
(the account-free path), may be unusable for a real deploy, or may be a quirk. **A stray project
`23658738-d8bd-4e34-a4e6-e72881f441a7` now exists from this probe and should be cleaned up.**

### 3. Reading the project back — blocked

Trying to query the project (owner/workspace/environments) to understand what an ownerless project
is was stopped by this session's safety classifier (flagged as probing a third-party service).
Paused here rather than work around it.

## Status: paused, need a decision

Unauthenticated `projectCreate` working is unexpected and I don't yet know whether it leads to a
usable, publicly-reachable deploy or is just an ephemeral anonymous project. I stopped probing
Railway's API further. Next step is a decision (see the message to the user), not more poking.

## Outcome

This investigation is why the benchmark now measures *Deploys without a human* directly (version 3):
rather than deciding per cloud whether an agent "needs a key", every deploy first runs with no
credentials and we record whether that alone produced a working app. Railway itself is not added
here; that's tracked separately.
