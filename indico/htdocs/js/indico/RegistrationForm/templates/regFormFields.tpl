<script type="text/template" id="itemWrapStd">
    <table class="{{ classes.fieldDisabled if field.disabled else classes.field }}" id="{{ field.id }}" >
        <tr>
          <td class="regFormCaption">
              <span class="regFormCaption">{{ field.caption }}</span>
              {% if field.mandatory %}
                    <span class="regFormMandatoryField">*</span>
              {% endif %}
          </td>
          <td>
              {{ item }}
          </td>
        </tr>
    </table>
</script>

<script type="text/template" id="itemWrapAllRight">
<table class="{{ classes.fieldDisabled if field.disabled else classes.field }}" id="{{ field.id }}">
    <tr>
      <td class="regFormCaption">
      </td>
      <td>
          {{ item }}
      </td>
    </tr>
</table>
</script>

<script type="text/template" id="text">
    {% if field.values.length != "" %}
        <input id="{{ name }}" type="text" name="{{ name }}" value=""  size="{{ field.values.length }}" {{ attributes }}>
    {% else %}
        <input id="{{ name }}" type="text" name="{{ name }}" value=""  size="60" {{ attributes }}>
    {% endif %}
        <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="country">
    <select id="{{ name }}" name="{{ name }}" {{ attributes }}>
        <option value="">{% _ '-- Select a country --' %}</option>
        {% for el in field.values.radioitems %}
            <option value="{{ el.countryKey }}">{{ el.caption }}</option>
        {% endfor %}
    </select>
    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="radio">
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
            {% if (el.placesLimit != 0 &&  el.noPlacesLeft == 0) %}
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
                <font color="green" style="font-style:italic; margin-left:25px;">{% _ '[{0} place(s) left]').format(el.noPlacesLeft %}</font>
            {% endif %}
        {% endfor %}
    {% endif %}

    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="file">
    <div id="attachment{{ name }}" class="existingAttachment">
        <input id="{{ name }}" name="{{ name }}" type="file" {{ attributes }}>
    </div>
    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="radiogroup">
<table class="blabla">
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
</script>

<script type="text/template" id="date">
    <span id="{{ name }}_DatePlace">
        <span class="dateField">
            <input type="text" {{ attributes }} ><img src="{{ imageSrc('calendarWidget') }}">
        </span>
    </span>
    <input type="hidden" value="" name="{{ name }}_Day" id="{{ name }}_Day">
    <input type="hidden" value="" name="{{ name }}_Month" id="{{ name }}_Month">
    <input type="hidden" value="" name="{{ name }}_Year" id="{{ name }}_Year">
    <input type="hidden" value="" name="{{ name }}_Hour" id="{{ name }}_Hour">
    <input type="hidden" value="" name="{{ name }}_Min" id="{{ name }}_Min">
    &nbsp;
    <span class="inputDescription">
        {% for el in field.values.displayFormats %}
            {% if (el[0] == field.values.dateFormat) %}
                {{ el[1] }}
            {% endif %}
        {% endfor %}
    </span>
    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="number">
    <input type="number" id="{{ name }}" name="{{ name }}" min="{{ field.values.minValue }}" class="{{ classes.billable if el.isBillable }}" value="{{ field.values.minValue }}" {{ attributes }} onchange="$E('subtotal-{{ name }}').dom.innerHTML = ((isNaN(parseInt(this.value, 10)) || parseInt(this.value, 10) &lt; 0) ? 0 : parseInt(this.value, 10)) * {{ field.price }};" size="{{ field.values.length }}">

    &nbsp;&nbsp;<span class="{{ classes.price }}">{{ field.price }}</span>&nbsp;<span class="{{ classes.currency }}"></span>
    <span class="regFormSubtotal">{% _ 'Total:' %}</span> <span id="subtotal-{{ name }}">0</span>
    &nbsp;<span class="{{ classes.currency }}"></span>

    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="yesno">
    <select id="{{ name }}" name="{{ name }}" {{ attributes }} class="{{ classes.billable if el.isBillable }}">
        <option value="">{% _ '-- Choose a value --' %}</option>
        <option value="yes">{% _ 'yes' %}&nbsp;
        {% if (field.placesLimit != 0) %}
            {% _ '[ {0} place(s) left]').format(field.noPlacesLeft %}
        {% endif %}
        </option>
        <option value="no">{% _ 'no' %}</option>
    </select>

    {% if (field.billable) %}
        <span class="{{ classes.price }}">{{ field.price }}</span>
        <span class="{{ classes.currency }}"></span>
    {% endif %}

    <span class="inputDescription">{{ field.description }}</span>

</script>

<script type="text/template" id="label">
    <div class="{{ classes.field }}" id="{{ field.id }}">
        {{ field.caption }}

        {% if (field.billable) %}
            &nbsp;&nbsp;&nbsp;
            <span class="{{ classes.price }}">{{ field.price }}</span>
            <span class="{{ classes.currency }}"></span>
        {% endif %}
        <span class="inputDescription">{{ field.description }}</span>
    </div>
</script>

<script type="text/template" id="textarea">
    <span class="inputDescription">{{ field.description }}</span><br>
    <textarea id="{{ name }}" name="{{ name }}" cols="{{ field.values.numberOfColumns }}" rows="{{ field.values.numberOfRows }}" {{ attributes }}></textarea>
</script>

<script type="text/template" id="checkbox">
    <input type="checkbox" id="{{ name }}" class="{{ classes.billable if field.isBillable }}" name="{{ name }}" {{ attributes }}>
    {{ field.caption }}
    {% if (field.billable) %}
        <span class="{{ classes.price }}">{{ field.price }}</span>
        <span class="{{ classes.currency }}"></span>
    {% endif %}
    {% if field.placesLimit != 0 and field.noPlacesLeft != 0 %}
        &nbsp;&nbsp;<span class="placesLeft">{% _ '[{0} place(s) left]').format(field.noPlacesLeft %}</span>
    {% elif field.placesLimit != 0 and field.noPlacesLeft == 0 %}
        &nbsp;&nbsp;<font color="red"> {% _ '(no places left)' %}</font>
    {% endif %}
    <span class="inputDescription">{{ field.description }}</span>
</script>

<script type="text/template" id="telephone">
    <input type="text" id="{{ name }}" name="{{ name }}" value="" size="30" {{ attributes }}>&nbsp;
    <span class="inputDescription">(+) 999 99 99 99</span>
    <span class="inputDescription">{{ field.description }}</span>
</script>
