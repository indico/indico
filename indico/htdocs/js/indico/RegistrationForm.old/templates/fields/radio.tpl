{% extends "regFormFields.tpl" %}

{% block field %}
    {% if (field.values.inputType == "dropdown") %}
        <select name="{{ name }}" {{ attributes }}>
            <option value="">{% _ '-- Choose a value --' %}</option>
            {% for el in field.values.radioitems %}
                {% set attributes = '' %}
                {% if el.placesLimit != 0 and el.noPlacesLeft == 0 %}
                   {% set attributes = 'disabled' %}
                {% elif field.values.defaultItem == el.caption %}
                   {% set attributes = 'selected' %}
                {% endif %}
                <option value="{{ el.id }}" {{ attributes }} class="{{ classes.billable if el.isBillable }}">
                    {{ el.caption }}
                </option>
            {% endfor %}
        </select>
    {% else %}
        {% for el in field.values.radioitems %}
            {% set disabled = false %}
            {% if el.placesLimit != 0 and el.noPlacesLeft == 0 %}
                {% set disabled = true %}
            {% endif %}
            <input type="radio" class="{{ classes.billable if el.isBillable }}" name="{{ name }}" value="{{ el.id }}" {{ attributes }} {{ "DISABLED" if disabled }}/>
            {{ el.caption }}
            {% if el.isBillable and not disabled %}
                <span class="{{ classes.price }}">{{ el.price }}</span>&nbsp;<span class="{{ classes.currency }}"></span>
            {% endif %}
            {% if disabled %}
                <font color="red" style="margin-left:25px;">{% _ "(no places left)" %}</font>
            {% elif el.placesLimit != 0 %}
                <font color="green" style="font-style:italic; margin-left:25px;">
                    [{{el.noPlacesLeft}} {% _ 'place(s) left' %}]
                </font>
            {% endif %}
        {% endfor %}
    {% endif %}

    <span class="inputDescription">{{ field.description }}</span>
{% endblock %}
