{% import "md/_macros.md" as m %}
# Runs

Every run of AI Deploy Bench, newest first. A full run covers every cloud, app and model; the others test a subset.

| Run | Scope | Models | Cells | Succeeded | Checks passed | Agent cost |
|---|---|---|---|---|---|---|
{% for run in runs | reverse %}
| [{{ run.label }}]({{ md(run.href) }}) | {{ run.scope | md_cell }} | {% for mo in run.info.get('models', []) %}{{ model_name(mo) }}{% if not loop.last %}, {% endif %}{% endfor %} | {{ run.cells | length }} | {{ run.success_count }} | {{ fmt.pct(run.mean_score) }} | {{ fmt.usd(run.agent_usd) }} |
{% endfor %}

{{ m.footer() }}
