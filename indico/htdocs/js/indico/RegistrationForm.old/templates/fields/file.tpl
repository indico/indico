{% extends "regFormFields.tpl" %}

{% block field %}
    <div id="attachment{{ name }}" class="existingAttachment">
        <input id="{{ name }}" name="{{ name }}" type="file" {{ attributes }}>
    </div>
    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
