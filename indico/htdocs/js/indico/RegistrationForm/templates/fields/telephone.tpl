{% extends "regFormFields.tpl" %}

{% block field %}
    <input type="text" id="{{ name }}" name="{{ name }}" value="" size="30" {{ attributes }}>
    <span class="inputDescription">(+) 999 99 99 99</span>
    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
