{% for photo in photos %}
    <a href="/{{ ident|urlencode }}/{{ photo }}/preview">{{ photo }}</a>
{% endfor %}
