{% extends "regFormSection.tpl" %}

{% block section %}
    <div class="{{ classes.content }}">
        <div>
            <p class="{{ classes.text }}">{{ section.description }}</p>
        </div>
        <textarea name="reason" rows="4" cols="80"></textarea>
    </div>
{% endblock %}
