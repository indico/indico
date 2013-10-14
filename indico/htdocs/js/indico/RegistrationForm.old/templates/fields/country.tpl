{% extends "regFormFields.tpl" %}

{% block field %}
    <select id="{{ name }}" name="{{ name }}" {{ attributes }}>
        <option value="">{% _ '-- Select a country --' %}</option>
        {% for el in field.values.radioitems %}
            <option value="{{ el.countryKey }}">{{ el.caption }}</option>
        {% endfor %}
    </select>
    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
