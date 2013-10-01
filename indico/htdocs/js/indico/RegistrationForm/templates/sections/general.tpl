{% extends "regFormSection.tpl" %}

{% block description %}
    <div class="{{ classes.description }}">
        {{ section.description }}
    </div>
{% endblock %}

{% block section %}
    <div class="{{ classes.content }} {{ classes.contentIsDragAndDrop }}">
        {% for field in fields %}
            {{ field }}
        {% endfor %}
    </div>
{% endblock %}
