{% extends "regFormFields.tpl" %}

{% block field %}
    <span id="{{ name }}_DatePlace">
        <span class="dateField">
            <input type="text" {{ attributes }} ><img src="{{ calendarimg }}">
        </span>
    </span>
    <input type="hidden" value="" name="{{ name }}_Day" id="{{ name }}_Day">
    <input type="hidden" value="" name="{{ name }}_Month" id="{{ name }}_Month">
    <input type="hidden" value="" name="{{ name }}_Year" id="{{ name }}_Year">
    <input type="hidden" value="" name="{{ name }}_Hour" id="{{ name }}_Hour">
    <input type="hidden" value="" name="{{ name }}_Min" id="{{ name }}_Min">

    <span class="inputDescription">
        {% for el in field.values.displayFormats %}
            {% if (el[0] == field.values.dateFormat) %}
                {{ el[1] }}
            {% endif %}
        {% endfor %}
    </span>

    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
