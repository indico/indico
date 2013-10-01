<div data-section-id="{{ section.id }}" class="{{ classes.section }}">
    <div class="{{ classes.header }}">
        <div class="{{ classes.title }}">{{ section.title }}</div>
        {% block description %}
        {% endblock %}
    </div>

    {% block section %}
    {% endblock %}
</div>
