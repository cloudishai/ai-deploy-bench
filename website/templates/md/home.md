{% import "md/_macros.md" as m %}
# AI Deploy Bench

> An open benchmark of what it takes for an AI coding agent to build a web app and deploy it to a cloud. {{ cfg.agent.get('name', 'Claude Code') }} builds {{ cfg.apps | length }} kinds of app from a written spec and deploys each to {% for c in cfg.clouds %}{{ c.name }}{% if loop.revindex == 2 %} and {% elif not loop.last %}, {% endif %}{% endfor %}. An independent verifier then tests each live deployment, and an independent review scores its security and the stack the agent chose.

Each app on each cloud is a *cell*, built and deployed by a fresh agent session on a fresh runner. Every run is a GitHub Actions workflow, and its results are committed to {{ github }}.

What it measures, per cloud: **success** (apps deployed and passing every required check), **deploys without a human** (apps deployed with no credentials provided, so no human signup or token), **human steps** and **human time** (what a person had to do for the agent to deploy), **security & compliance** and **stack fit** (0-100 scores from an independent review), build and deploy **time**, **tokens** and **agent cost**, and the expected monthly **hosting** cost with light use and when busy. Definitions: {{ md('/methodology/') }}

{% if latest %}
## {{ 'Latest results' if latest.full else 'Latest run' }}

{{ m.run_line(latest) }}. Details: {{ md(latest.href) }}

{% for model in latest.info.get('models', []) %}
{% if latest.info.models | length > 1 %}### {{ model_name(model, True) }}

{% endif %}
{{ m.compare_table(latest, model) }}

Each app on each cloud (links open that cell's report):

{{ m.matrix(latest, model) }}
{% endfor %}
{% endif %}
## Clouds

{% for cloud in cfg.clouds %}
- [{{ cloud.name }}]({{ md(cloud_href(cloud.id)) }}): what a person had to do, each app's results and every run ({{ cloud.url }})
{% endfor %}

## More

- Every run: {{ md('/runs/') }}
- Trends of each metric over runs: {{ md('/trends/') }}
- Methodology: {{ md('/methodology/') }}

{{ m.footer() }}
