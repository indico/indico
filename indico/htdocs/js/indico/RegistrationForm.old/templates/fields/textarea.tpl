{% extends "regFormFields.tpl" %}

{% block field %}
    <span class="inputDescription">
        {{ field.description }}
    </span>
    <textarea id="{{ name }}" name="{{ name }}" cols="{{ field.values.numberOfColumns }}" rows="{{ field.values.numberOfRows }}" {{ attributes }}></textarea>
{% endblock %}
