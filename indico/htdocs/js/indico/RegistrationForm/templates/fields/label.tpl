{% extends "regFormFields.tpl" %}

{% block field %}
    <div class="{{ classes.field }}" id="{{ field.id }}">
        {{ field.caption }}

        {% if (field.billable) %}
            <span class="{{ classes.price }}">{{ field.price }}</span>
            <span class="{{ classes.currency }}"></span>
        {% endif %}
        <span class="inputDescription">{{ field.description }}</span>
    </div>
{% endblock %}
