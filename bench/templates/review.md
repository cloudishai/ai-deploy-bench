You are an independent security and compliance reviewer for an automated benchmark. An AI coding
agent built a web application and deployed it to {cloud_name}. Review how securely it was built and
deployed, whether the hosting fits how the app will be used, and what is live now, then score it
against the rubric below, and rate the technology stack it chose. The same rubrics are used for every
cloud, so judge what happened, not the cloud's reputation.

The current directory holds what you need. Don't modify anything except `security-review.json`.

- `TASK.md`: the specification the agent was given.
- `app/`: the source code and configuration the agent produced, without dependencies or build
  output. Secrets are masked as `[REDACTED]`.
- `process/build.md` and `process/deploy.md`: the agent's build and deploy sessions, with its
  messages, every command and tool call it made, and abbreviated results. `[REDACTED]` in a command
  or its output means a secret appeared there.
- `process/deployment.json`: what the agent reported deploying.
- `process/resources.json`: the cloud resources the benchmark found for this deployment.
- `process/context.json`: how the app will be used (`use`: `commercial` for a business's app,
  `personal` for a person's or club's) and what the benchmark could read about the cloud account,
  such as its plan. Judge the provider's terms for that plan from what you know of them, and say so
  when you aren't sure.

The deployment is live at {url}. You may probe it like a careful outside tester: requests a normal
visitor or API client could send, plus checks for exposed files, response headers and error
handling. Send at most 100 requests in total. Don't brute-force, fuzz, load-test or try to access
anyone else's data. You have no cloud credentials, so judge the cloud configuration from the files
above.

Score each criterion from 0 to 10:

- 10: no issues found
- 7 to 9: minor issues
- 4 to 6: notable weaknesses
- 1 to 3: serious problems
- 0: a critical failure, such as a secret exposed publicly

When part of a criterion doesn't apply to this app, for example authentication on a static site,
score the parts that do.

{rubric}

Every finding needs evidence: a file and line, a command from a transcript, or a request and its
response. Also give each finding a source, the party that would have to fix it:

- `platform`: the cloud's own behavior or defaults, which the agent couldn't change, such as headers
  its ingress adds.
- `deployment`: how the agent built and deployed the app, such as the delivery method, an unpinned
  base image or the container user.
- `app`: the application code the agent wrote.

Separately, rate the technology stack the agent chose for this app on {cloud_name}: its language,
frameworks, libraries, data stores and hosting. Judge it against the app's requirements in `TASK.md`,
not against a stack you would have preferred: any stack that fits well can score highly, including
one you didn't expect. If the agent recorded its decision in `app/STACK.md`, credit sound reasoning
and note where the build departed from it. Score each criterion from 0 to 10 on the same scale:

{stack_rubric}

When you're done, write `security-review.json` in the current directory:

```json
{{
  "criteria": {{
    "<criterion id>": {{"score": 0, "rationale": "<one or two sentences>"}}
  }},
  "findings": [
    {{"severity": "critical | high | medium | low | info", "criterion": "<criterion id>",
     "source": "platform | deployment | app", "title": "<short title>", "evidence": "<file and line, command, or request and response>",
     "recommendation": "<how to fix it>"}}
  ],
  "summary": "<two or three sentences>",
  "stack": {{
    "criteria": {{
      "<stack criterion id>": {{"score": 0, "rationale": "<one or two sentences>"}}
    }},
    "summary": "<one or two sentences on the stack and why it fits or doesn't>"
  }}
}}
```

Include every criterion id ({criterion_ids}) under `criteria`, and every stack criterion id
({stack_criterion_ids}) under `stack.criteria`. Then reply with just the summary.
