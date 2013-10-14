{% extends "regFormSection.tpl" %}

{% block description %}
    <div class="{{ classes.description }}">{{ section.description }}</div>
{% endblock %}

{% block section %}
<div class="{{ classes.content }}">
    <table>
        <tr>
            <td align="left" colspan="3" class="regFormSubGroupTitle" style="padding-bottom:20px">{{ section.introSentence }}</td>
        </tr>
        {% for item in section.items %}
            <tr>
            {% if item.cancelled %}
                 <td class="regFormSectionLeftSpacing1">
                    <b>-</b> {{ item.caption }} <font color="red">({{ item.cancelledReason }})</font>
                 </td>
            {% elif item.placesLimit != 0 and item.noPlacesLeft == 0 %}
                <td class="regFormSectionLeftSpacing1">
                    {% if section.selectionType == "multiple" %}
                        <input type="checkbox" name="socialEvents" value="{{ item.id }}" disabled/>
                        {{ item.caption }}
                    {% else %}
                        <input type="radio" name="socialEvents" value="{{ item.id }}" disabled/>
                        {{ item.caption }}
                    {% endif %}
                    <font color="red">{% _ '(no places left)' %}</font>
                 </td>
            {% else %}
                <td class="regFormSectionLeftSpacing1">
                    {% if section.selectionType == "multiple" %}
                        <input type="checkbox" class="{{ classes.billable if item.billable }}" name="socialEvents" value="{{ item.id }}"/>
                        {{ item.caption }}
                    {% else %}
                        <input type="radio" class="{{ classes.billable if item.billable }}" name="socialEvents" value="{{ item.id }}"/>
                        {{ item.caption }}
                    {% endif %}
                </td>
                <td>
                    <select name="places-{{ item.id }}">
                        {% if item.placesLimit != 0 %}
                            {% set maxReg = Math.min(item.maxPlacePerRegistrant,item.noPlacesLeft) %}
                        {% else %}
                            {% set maxReg = item.maxPlacePerRegistrant %}
                        {% endif %}
                        {% for i in range(maxReg) %}
                            <option value="{{ i }}">{{ i }}</option>
                        {% endfor %}
                    </select>
                    {% if item.placesLimit != 0 %}
                        <span class="placesLeft">
                            {{ $T('[{0} place(s) left]').format(item.noPlacesLeft) }}
                        </span>
                    {% endif %}
                </td>
                {% if item.billable %}
                    <td align="right">
                        <span class="{{ classes.price }}">{{ item.price }}</span>
                        <span class="{{ classes.currency }}"></span>
                        {% if item.isPricePerPlace %}
                            {% _ "per place" %}
                        {% endif %}
                    </td>
                {% endif %}
            {% endif %}
            </tr>
        {% endfor %}
    </table>
</div>
{% endblock %}
