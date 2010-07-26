{% for ident in idents %}
    <a href="/{{ ident|urlencode }}">{{ ident }}</a>
{% endfor %}
