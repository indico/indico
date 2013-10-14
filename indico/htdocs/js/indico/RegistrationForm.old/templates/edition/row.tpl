<tbody>
    <tr role="row" id="{{ item.id }}">

        {% if config.actions.indexOf("sortable") > -1 %}
        <td>
            <span class="ui-icon ui-icon-arrowthick-2-n-s"></span>
        </td>
        {% endif %}

        {% for el in config.colModel %}
            <td role="gridcell" style="text-align: {{ el.align }};" name="{{ el.name }}" title="{{ item[el.index] }}">
                {% if el.editable == undefined and el.editable == false %}
                    {{ item[el.index] }}
                {% elif el.edittype == "text" and el.edittype == undefined %}
                    <input type="text" size="{{ el.editoptions.size }}" maxlength="{{ el.editoptions.maxlength }}" name="{{ el.name }}" class="editable" value="{{ item[el.index] }}">
                {% elif el.edittype == "bool_select" %}
                    <select name="{{ el.name }}" size="1" class="editable">
                        {% set selected = el.defaultVal; %}
                        {% if not _.isUndefined(item[el.index]) %}
                            {% set selected = item[el.index] %}
                        {% endif %}
                        <option role="option" value="true" {{ "selected" if selected }}>
                            {% _ "yes" %}
                        </option>
                        <option role="option" value="false" {{ "selected" if selected }}>
                            {% _ "no" %}
                        </option>
                    </select>
                {% elif el.edittype == "radio" %}
                    <input type="radio" name="{{ el.name }}"/>
                {% endif %}
            </td>
        {% endfor %}

        {% if config.actions.indexOf("remove") > -1 %}
        <td>
            <button class="actionTrash">{% _ "Remove" %}</button>
        </td>
        {% endif %}

        {% for action in config.actions %}
            {% if _.isArray(action) %}
                <td>
                    <button ref="{{ action[1] }}" class="actionTabSwitch ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only" role="button" aria-disabled="false" title="{{ action[0] }}">
                        <span class="ui-button-icon-primary ui-icon {{ action[2] }}"></span>
                        <span class="ui-button-text">"{{ action[0] }}"</span>
                    </button>
                </td>
            {% endif %}
        {% endfor %}
    </tr>
</tbody>
