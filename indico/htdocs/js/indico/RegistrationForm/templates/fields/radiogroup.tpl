{% extends "regFormFields.tpl" %}

{% block field %}
    <table>
        <tr>
            <td align="right" colspan="2">
            </td>
        </tr>

        {% for el in field.values.radioitems %}
        <tr>
            <td>
            </td>
            <td>
                <input type="radio" id="{{ name }}_{{ ind }}" name="{{ name }}" value="{{ el.id }}" {{ attributes }}/>
                {{ el.caption }}
            </td>
        </tr>
        {% endfor %}

        <tr>
            <td>
            </td>
            <td colspan="2">
                <span class="inputDescription">{{ field.description }}</span>
            </td>
         </tr>
    </table>
{% endblock %}
