{% import "md/_macros.md" as m %}
# Run {{ run.label }}

> {{ m.run_line(run) }} · {{ run.info.get('trials', 1) }} trial(s) per cell. {{ run.success_count }} of {{ run.finished | length }} cells succeeded.

- Web page: {{ url(run.href) }}
- Summary (JSON): {{ url('/data/runs/' ~ run.name ~ '/summary.json') }}
{% if run.info.get('url') %}
- Workflow run, with transcripts: {{ run.info.url }}
{% endif %}
{% if run.info.get('base_run') %}
- This run reran {{ run.info.get('rerun') }}; the other cells are copied unchanged from run [#{{ run.info.base_run.number }}]({{ md('/runs/' ~ run.info.base_run.name ~ '/') }}).
{% endif %}

{% for model in run.info.get('models', []) %}
## By cloud{% if run.info.models | length > 1 %} · {{ model_name(model, True) }}{% endif %}

{% if not run.full %}A partial run: {{ run.scope | lower }}. Totals cover those apps only.

{% endif %}
{{ m.compare_table(run, model) }}

## By app{% if run.info.models | length > 1 %} · {{ model_name(model, True) }}{% endif %}

{{ m.matrix(run, model) }}
{% endfor %}
## All cells

| Cloud | App | Model | Trial | Result | Checks | Without a human | Human steps | Human time | Security | Stack fit | Build | Deploy | Tokens | Agent cost |{% for u in cfg.hosting_usage %} Hosting, {{ u.label | lower }} |{% endfor %}

|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|{% for u in cfg.hosting_usage %}---|{% endfor %}

{% for cell in run.cells %}
| {{ cloud_name(cell.cloud) }} | {{ app_name(cell.app) }} | {{ model_name(cell.model) }} | {{ cell.trial }} | {{ m.result(cell) }} | {{ cell.checks_passed }}/{{ cell.checks_total }} | {{ outcomes[cell.without_human][1] if cell.without_human else '—' }} | {{ fmt.count(cell.human_steps | length if cell.human_steps is not none else None) }} | {{ fmt.minutes(cell.human_minutes) }} | {{ fmt.score(cell.security_score) }} | {{ fmt.score(cell.stack_fit_score) }} | {{ fmt.duration(cell.build_s) }} | {{ fmt.duration(cell.deploy_s) }} | {{ fmt.tokens(cell.tokens) }} | {{ fmt.usd(cell.agent_usd) }} |{% for label, cost in hosting(cell.summary) %} {{ cost }} |{% endfor %}

{% endfor %}

{{ m.footer() }}
