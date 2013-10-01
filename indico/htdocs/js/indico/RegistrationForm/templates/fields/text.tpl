{% extends "regFormFields.tpl" %}

{% block field %}
    {% if field.values.length != "" %}
        <input id="{{ name }}" type="text" name="{{ name }}" value=""  size="{{ field.values.length }}" {{ attributes }}>
    {% else %}
        <input id="{{ name }}" type="text" name="{{ name }}" value=""  size="60" {{ attributes }}>
    {% endif %}
    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
