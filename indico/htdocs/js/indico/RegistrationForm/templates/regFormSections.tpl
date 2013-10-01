<div data-section-id="{{ section.id }}" class="{{ classes.section }}" >
    <div class="{{ classes.header }}">
        <div class="{{ classes.title }}">{{ section.title }}</div>
        {% if section.id != "reasonParticipation" and section.id != "furtherInformation" %}
            <div class="{{ classes.description }}">{{ section.description }}</div>
        {% endif %}
    </div>

    <!-- further information form -->
    {% if section.id == "furtherInformation" %}
        <div class="{{ classes.content }}">
            <div>
                <p class="{{ classes.text }}">{{ section.content }}</p>
            </div>
        </div>

    <!-- Participation reason form -->
    {% elif section.id == "reasonParticipation" %}
        <div class="{{ classes.content }}">
            <div>
                <p class="{{ classes.text }}">{{ section.description }}</p>
            </div>
            <textarea name="reason" rows="4" cols="80"></textarea>
        </div>

    <!-- session form -->
    {% elif section.id == "sessions" %}
        <div class="{{ classes.content }}">
            {% if section.type == "2priorities" %}
            <table>
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
            </table>
            {% else %}
            <table>
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
            </table>
            {% endif %}
        </div>

     <!-- accommodation form -->
     {% elif section.id == "accommodation" %}
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

    <!-- social events form -->
    {% elif section.id == "socialEvents" %}
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

    <!-- General form -->
    {% else  %}
    <div class="{{ classes.content }} {{ classes.contentIsDragAndDrop }}">
        {% for i in range(section.items.length) %}
            {% set field = section.items[i] %}
            {{ fields.render(field, section.id) }}
        {% endfor %}
    </div>
    {% endif %}
</div>
