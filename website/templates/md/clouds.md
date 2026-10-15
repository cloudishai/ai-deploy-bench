{% import "md/_macros.md" as m %}
# Clouds

Each cloud gets the same {{ cfg.apps | length }} apps, built and deployed by a fresh agent session each. Each cloud's page has what a person had to do, each app's results and every run.

{% for cloud in cfg.clouds %}
- [{{ cloud.name }}]({{ md(cloud_href(cloud.id)) }}) ({{ cloud.url }})
{% endfor %}

{% if latest %}
## {{ 'Latest full run' if latest.full else 'Latest run' }}: {{ latest.label }}

{% for model in latest.info.get('models', []) %}
{{ m.compare_table(latest, model) }}
{% endfor %}
{% endif %}

{{ m.footer() }}
