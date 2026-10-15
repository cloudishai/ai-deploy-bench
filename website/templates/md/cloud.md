{% import "md/_macros.md" as m %}
# {{ cloud_name(cloud) }}

> How an AI coding agent did building and deploying {{ cfg.apps | length }} apps on {{ cloud_name(cloud) }}{% if cloud_url(cloud) %} ({{ cloud_url(cloud) }}){% endif %}, in {{ history | length }} run(s) of AI Deploy Bench.

Web page: {{ url(cloud_href(cloud)) }}

{% if latest %}
{% for model in latest.info.get('models', []) %}
{% set g = latest.group(model, cloud) %}
{% set cells = latest.cloud_cells(model, cloud) %}
{% if g %}
{% set people = human(g) %}
## Latest results{% if latest.info.models | length > 1 %} · {{ model_name(model, True) }}{% endif %}

{{ m.run_line(latest) }}. All clouds in this run: {{ md(latest.href) }}

{% if latest.inherited(model, cloud) %}
This run reran other clouds, so these results are copied unchanged from run [#{{ cells[0].from_run.number }}]({{ md('/runs/' ~ cells[0].from_run.name ~ '/') }}).

{% endif %}
- Success: {{ g.get('success', 0) }}/{{ g.get('cells', 0) }} apps deployed and passing every required check
{% if g.get('deploys_without_human') %}
- Deploys without a human: {{ g.deploys_without_human.count }}/{{ g.deploys_without_human.total }} (deployed with no credentials provided: no signup or token)
{% endif %}
- Human steps: {{ fmt.count(people[0]) }}, about {{ fmt.minutes(people[1]) }} of a person's time, once per account
- Checks passed: {{ fmt.pct(g.get('mean_score')) }}
- Security & compliance: {{ fmt.score(g.get('security_score')) }}
{% if g.get('stack_fit_score') is not none %}
- Stack fit: {{ fmt.score(g.get('stack_fit_score')) }}
{% endif %}
- Average build: {{ fmt.duration(g.get('mean_build_s')) }}; average deploy: {{ fmt.duration(g.get('mean_deploy_s')) }} (per app)
- Agent cost: {{ fmt.usd(g.get('agent_usd')) }} ({{ fmt.tokens(g.get('tokens')) }} tokens, all apps)
- Hosting per month: {% for label, cost in hosting(g) %}{{ cost }} {{ label | lower }}{% if not loop.last %}, {% endif %}{% endfor %}


## What a person had to do

{% set steps = human_steps(cells) %}
{% if steps %}
Before the agent could deploy, a person had to do, or would have to do, the following. Each is done once per account.

| Step | Minutes | Needed for |
|---|---|---|
{% for step in steps %}
| {{ step.description | md_cell }} | {{ fmt.minutes(step.minutes) }} | {{ step.apps }} of {{ cells | length }} apps |
{% endfor %}
{% else %}
Nothing. The agent signed up and got its own credentials, with no person involved.
{% endif %}

Every deploy is first tried with no credentials. When that can't finish, the cloud's credentials are provided and the same session tries again.

## Each app

| App | Result | Without a human | Checks | Human steps | Security | Stack fit | Build | Deploy | Agent cost | Hosting | Built with |
|---|---|---|---|---|---|---|---|---|---|---|---|
{% for cell in cells %}
| {{ app_name(cell.app) }} | {{ m.result(cell) }} | {{ outcomes[cell.without_human][1] if cell.without_human else '—' }} | {{ cell.checks_passed }}/{{ cell.checks_total }} | {{ fmt.count(cell.human_steps | length if cell.human_steps is not none else None) }} · {{ fmt.minutes(cell.human_minutes) }} | {{ fmt.score(cell.security_score) }} | {{ fmt.score(cell.stack_fit_score) }} | {{ fmt.duration(cell.build_s) }} | {{ fmt.duration(cell.deploy_s) }} | {{ fmt.usd(cell.agent_usd) }} | {% for label, cost in hosting(cell.summary) %}{{ cost }} {{ label | lower }}{% if not loop.last %}, {% endif %}{% endfor %} | {{ cell.stack_headline | join(', ') | md_cell }} |
{% endfor %}

Each app's report has its checks, security review, cost breakdown, the commands the agent ran and screenshots.

{% endif %}
{% endfor %}
{% endif %}
## Every run

{% if history %}
| Run | Scope | Model | Success | Without a human | Checks | Human steps | Security | Agent cost |{% for app in cfg.apps %} {{ app.short or app.name }} |{% endfor %}

|---|---|---|---|---|---|---|---|---|{% for app in cfg.apps %}---|{% endfor %}

{% for run in history | reverse %}
{% for model in run.info.get('models', []) %}
{% set g = run.group(model, cloud) %}
{% if g %}
{% set people = human(g) %}
| [{{ run.label }}]({{ md(run.href) }}){% if run.inherited(model, cloud) %} (copied from #{{ run.cloud_cells(model, cloud)[0].from_run.number }}){% endif %} | {{ 'Full run' if run.full else run.scope | md_cell }} | {{ model_name(model) }} | {{ g.get('success', 0) }}/{{ g.get('cells', 0) }} | {% if g.get('deploys_without_human') %}{{ g.deploys_without_human.count }}/{{ g.deploys_without_human.total }}{% else %}—{% endif %} | {{ fmt.pct(g.get('mean_score')) }} | {{ fmt.count(people[0]) }} · {{ fmt.minutes(people[1]) }} | {{ fmt.score(g.get('security_score')) }} | {{ fmt.usd(g.get('agent_usd')) }} |{% for app in cfg.apps %} {{ m.result(run.cell(model, cloud, app.id)) }} |{% endfor %}

{% endif %}
{% endfor %}
{% endfor %}
{% else %}
No run has included {{ cloud_name(cloud) }} yet.
{% endif %}

{{ m.footer() }}
