{% extends "regFormFields.tpl" %}

{% block field %}
    <select id="{{ name }}" name="{{ name }}" {{ attributes }} class="{{ classes.billable if el.isBillable }}">
        <option value="">
            {% _ '-- Choose a value --' %}
        </option>
        <option value="yes">
            {% _ 'yes' %}
            {% if field.placesLimit != 0 %}
                [{{field.noPlacesLeft}} {% _ 'place(s) left' %}]
            {% endif %}
        </option>
        <option value="no">
            {% _ 'no' %}
        </option>
    </select>

    {% if field.billable %}
        <span class="{{ classes.price }}">{{ field.price }}</span>
        <span class="{{ classes.currency }}"></span>
    {% endif %}

    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
