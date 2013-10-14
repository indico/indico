{% extends "regFormSection.tpl" %}

{% block description %}
    <div class="{{ classes.description }}">{{ section.description }}</div>
{% endblock %}

{% block section %}
<div class="{{ classes.content }}">
    <table>
        <tr>
            <td>
                <table>
                    <tr>
                        <td align="left">
                            <span>{% _ 'Arrival date' %}</span>
                            <span class="regFormMandatoryField">*</span>
                        </td>
                        <td align="left"  class="regFormPadding1">
                            <select id="arrivalDate" name="arrivalDate" required>
                                <option value="" selected="">{% _ '--select a date--' %}</option>
                                {% for date in section.arrivalDates %}
                                    <option value="{{ date[0] }}">{{ date[1] }}</option>
                                {% endfor %}
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td align="left">
                            <span>Departure date</span>
                            <span class="regFormMandatoryField">*</span>
                        </td>
                        <td align="left"  class="regFormPadding1">
                            <select id="departureDate" name="departureDate" required>
                                    <option value="" selected="">{% _ '--select a date--' %}</option>
                                    {% for date in section.departureDates %}
                                        <option value="{{ date[0] }}">{{ date[1] }}</option>
                                    {% endfor %}
                            </select>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                <table>
                    <tbody>
                        <tr>
                            <td>
                                <span id="accommodationTypeLabel" class="regFormSubGroupTitle">
                                    {% _ 'Select your accommodation' %}
                                </span>
                                <span class="regFormMandatoryField">*</span>
                            </td>
                        </tr>
                        {% for item in section.items %}
                            <tr>
                                <td align="left" class="regFormSectionLeftSpacing1">
                                    {% if item.cancelled %}
                                        {% set attributes = "disabled" %}
                                    {% elif item.placesLimit != 0 and item.noPlacesLeft == 0 %}
                                        {% set attributes = "disabled" %}
                                    {% else %}
                                        {% set attributes = "required" %}
                                    {% endif %}

                                    <input type="radio" id="{{ item.id }}" class="{{ classes.billable if item.billable }}" name="accommodation_type" value="{{ item.id }}" {{ attributes }}/>
                                    {{ item.caption }}

                                    {% if item.cancelled %}
                                        <font color="red"> {% _ '(not available at present)' %}</font>
                                    {% elif item.placesLimit != 0 and item.noPlacesLeft == 0 %}
                                        <font color="red">{% _ '(no places left)' %}</font>
                                    {% elif item.placesLimit != 0 %}
                                        <font color="green" style="font-style:italic;">[{{ item.noPlacesLeft }} {{ "place(s) left" | _}}]</font>
                                    {% endif %}
                                </td>
                                <td align="right" style="padding-left:20px;">
                                    {% if item.billable %}
                                        <span class="{{ classes.price }}">{{ item.price }}</span>
                                        <span class="{{ classes.currency }}"></span>
                                        <span>{% _ "per night" %}</span>
                                    {% endif %}
                                </td>
                            </tr>
                        {% endfor %}
                </table>
            </td>
        </tr>
    </table>
</div>
{% endblock %}
