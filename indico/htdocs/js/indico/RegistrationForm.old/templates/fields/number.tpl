{% extends "regFormFields.tpl" %}

{% block field %}
    <input type="number" id="{{ name }}" name="{{ name }}" min="{{ field.values.minValue }}" class="{{ classes.billable if el.isBillable }}" value="{{ field.values.minValue }}" {{ attributes }} onchange="$E('subtotal-{{ name }}').dom.innerHTML = ((isNaN(parseInt(this.value, 10)) || parseInt(this.value, 10) &lt; 0) ? 0 : parseInt(this.value, 10)) * {{ field.price }};" size="{{ field.values.length }}"/>

    <span class="{{ classes.price }}">{{ field.price }}</span>
    <span class="{{ classes.currency }}"></span>
    <span class="regFormSubtotal">{% _ 'Total:' %}</span>
    <span id="subtotal-{{ name }}">0</span>
    <span class="{{ classes.currency }}"></span>
    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
