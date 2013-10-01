{% extends "regFormFields.tpl" %}

{% block field %}
    <input type="checkbox" id="{{ name }}" class="{{ classes.billable if field.isBillable }}" name="{{ name }}" {{ attributes }}/>

    {{ field.caption }}

    {% if field.billable %}
        <span class="{{ classes.price }}">{{ field.price }}</span>
        <span class="{{ classes.currency }}"></span>
    {% endif %}

    {% if field.placesLimit != 0 and field.noPlacesLeft != 0 %}
        <span class="placesLeft">
            [{{field.noPlacesLeft}} {% _ 'place(s) left' %}]
        </span>
    {% elif field.placesLimit != 0 and field.noPlacesLeft == 0 %}
        <font color="red"> {% _ '(no places left)' %}</font>
    {% endif %}

    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
