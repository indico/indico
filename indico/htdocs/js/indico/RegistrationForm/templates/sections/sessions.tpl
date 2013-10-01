{% extends "regFormSection.tpl" %}

{% block description %}
    <div class="{{ classes.description }}">{{ section.description }}</div>
{% endblock %}

{% block section %}
    <div class="{{ classes.content }}">
        <table>
        {% if section.type == "2priorities" %}
            <tr>
                <td>
                    <span>
                        {% _ 'Select your preferred choice' %}
                    </span>
                    <span class="regFormMandatoryField">*</span>
                </td>
                <td class="regFormSectionLeftSpacing1">
                    <select id="session1" name="session1" required>
                        <option value="" selected="">{% _ '--Select a session--' %}</option>
                        {% for item in section.items %}
                            <option value="{{ item.id }}">{{ item.caption }}</option>
                        {% endfor %}
                    </select>
                </td>
            </tr>
            <tr>
                <td>
                    <span>{% _ 'Select your second choice' %}</span>
                    <span class="regFormItalic">(Optional)</span>
                </td>
                <td class="regFormSectionLeftSpacing1">
                    <select id="session2" name="session2">
                        <option value="nosession" selected="">{% _ '--Select a session--' %}</option>
                        {% for item in section.items %}
                            <option value="{{ item.id }}">{{ item.caption }}</option>
                        {% endfor %}
                    </select>
                </td>
            </tr>
        {% else %}
            <tr>
                <td class="regFormSectionLeftSpacing1" colspan="3">
                    {% for item in section.items %}
                        <input class="{{ classes.billable if item.billable }}" type="checkbox" name="sessions" value="{{ item.id }}"/>
                        {{ item.caption }}
                        {% if item.billable %}
                            <span class="{{ classes.price }}">{{ item.price }}</span>
                            <span class="{{ classes.currency }}"></span>
                        {% endif %}
                        <br>
                    {% endfor %}
                <td>
            </tr>
        {% endif %}
        </table>
    </div>
{% endblock %}
