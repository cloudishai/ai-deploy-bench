{# Markdown pieces shared by the pages' markdown versions. Links are absolute, so a page reads the same wherever it's fetched from. #}
{% macro compare_table(run, model) -%}
| Metric | {% for cloud in run.clouds() %}[{{ cloud_name(cloud) }}]({{ md(cloud_href(cloud)) }}) | {% endfor %}

|---|{% for cloud in run.clouds() %}---|{% endfor %}

{% for row in compare(run, model) -%}
| {{ row.label }} | {% for v in row['values'] %}{{ '**' ~ v.text ~ '**' if v.best else v.text }} | {% endfor %}

{% endfor %}

The best value in each row is in bold. Lower is better for human steps, human time, times, tokens and costs; higher for the rest.
{%- endmacro %}

{% macro result(cell) -%}
{%- if cell and cell.status != 'missing' %}[{{ states[state(cell)][0] }}]({{ md(cell.href) }}){% elif cell %}Missing{% else %}—{% endif %}
{%- endmacro %}

{% macro matrix(run, model) -%}
| App | {% for cloud in run.clouds() %}{{ cloud_name(cloud) }} | {% endfor %}

|---|{% for cloud in run.clouds() %}---|{% endfor %}

{% for app in run.apps() -%}
| {{ app_name(app) }} | {% for cloud in run.clouds() %}{{ result(run.cell(model, cloud, app)) }} | {% endfor %}

{% endfor %}
{%- endmacro %}

{% macro run_line(run) -%}
Benchmark run {{ run.label }} ({{ run.scope | lower }}) · {% for m in run.info.get('models', []) %}{{ model_name(m, True) }}{% if not loop.last %}, {% endif %}{% endfor %}{% if run.info.get('benchmark_version') %} · benchmark v{{ run.info.benchmark_version }}{% endif %}{% if run.info.get('agent_versions') %} · Claude Code {{ run.info.agent_versions | join(', ') }}{% endif %}
{%- endmacro %}

{% macro footer() -%}
---

Site: {{ url('/') }} · Index for language models: {{ url('/llms.txt') }} · Raw results (JSON): {{ url('/data/index.json') }} · Methodology: {{ md('/methodology/') }} · Source: {{ github }}
{%- endmacro %}
