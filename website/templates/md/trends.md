{% import "md/_macros.md" as m %}
# Trends{% if app %}: {{ app_name(app, False) }}{% endif %}

{% if app %}How each metric changed for the {{ app_name(app) | lower }}, in every run that included it, one column per cloud (averaged over trials).{% else %}How each metric changed across all apps, over every full run, one column per cloud.{% endif %} Runs copied from an earlier run by a partial rerun are left out (—). Web page with charts: {{ url('/trends/' ~ (app ~ '/' if app else '')) }}

{% for chart in charts %}
## {{ chart.metric.label }}

{{ chart.metric.description }} {{ 'Higher' if chart.metric.better == 'higher' else 'Lower' }} is better.

{% if chart.series %}
| Run | {% for s in chart.series %}{{ s.name }} | {% endfor %}

|---|{% for s in chart.series %}---|{% endfor %}

{% for run in chart.runs %}
{% set i = loop.index0 %}
| [{{ run.label }}]({{ md(run.href) }}) | {% for s in chart.series %}{{ chart.metric.format(s['values'][i]) }} | {% endfor %}

{% endfor %}
{% else %}
No data yet.
{% endif %}

{% endfor %}
Per app: {% for a in cfg.apps %}[{{ a.short or a.name }}]({{ md('/trends/' ~ a.id ~ '/') }}){% if not loop.last %} · {% endif %}{% endfor %}


{{ m.footer() }}
