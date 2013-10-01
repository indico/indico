{# TODO #}
<script type="text/template" id="disabledFields">
    {% for i in range(section.items.length) %}
        {% set field = section.items[i] %}
        {% if field.disabled %}
            {{ fields.render(field, section.id) }}
        {% endif %}
    {% endfor %}
</script>
