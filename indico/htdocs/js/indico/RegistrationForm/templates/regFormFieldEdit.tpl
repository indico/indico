<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        <li class="active">
            <a data-toggle="tab" id="tab-options" ref="#div-options">{% _ 'Options' %}</a>
        </li>
        {% if field.input == "radio" %}
        <li>
            <a data-toggle="tab" id="tab-editItems" ref="#div-editItems">{% _ 'Edit items' %}</a>
        </li>
        {% endif %}
    </ul>
    <div class="tab-content regFormDialogTabContent">
        <div class="tab-pane active" id="div-options">
            <form id="optionsForm">
            <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'caption' %}</label>
                <input type="text" name="caption" id="input01" size="30" value="{{ field.caption }}" required>
                {% if field.mandatory %}
                    {% set status = "CHECKED" %}
                {% endif %}
                {% if _.indexOf(field.lock, "mandatory") > -1 %}
                    {% set status  = status +" DISABLED" %}
                {% endif %}
                <input type="checkbox" name="mandatory" id="input02" {{ status }}/> {% _ 'Mandatory' %}
           </div>

           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'description' %}</label>
                <textarea id="descriptionEdit" name="description" cols="40" rows="5">{{ any(field.description,'') }}</textarea>
           </div>

           {% if field.input == "telephone" or field.input == "text" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'size in char' %}</label>
                <input name="length" type="number" size="20" min="5" max="60" value="{{ field.values.length if field.values.length != 'undefined' }}">
                <span>{% _ "(Must be between 5 and 60)" %}</span>
           </div>
           {% endif %}

           {% if field.input == "textarea" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'number of columns' %}</label>
                <input name="numberOfColumns" type="number" min=1 size="20" value="{{ any(field.values.numberOfColumns,'') }}">
           </div>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'number of rows' %}</label>
                <input name="numberOfRows" type="number" min=1 size="20" value="{{ any(field.values.numberOfRows,'') }}">
           </div>
           {% endif %}

           {% if field.input == "number" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'minimum value' %}</label>
                <input name="minValue" type="number" size="20" value="{{ any(field.values.minValue,'') }}">
           </div>
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'row length' %}</label>
                <input name="numberOfRows" type="number" min=0 size="20" value="{{ any(field.values.length,'') }}">
           </div>
           {% endif %}

           {% if field.input == "yesno" or field.input == "checkbox" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'places limit' %}</label>
                <input name="placesLimit" type="number" size="20" min=0 value="{{ any(field.placesLimit,'') }}">
                <span>{% _ "(0 for unlimited)" %}</span>
           </div>
           {% endif %}

           {% if field.input == "yesno" or field.input == "number" or field.input == "label" or field.input == "checkbox" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'Billable' %}</label>
                <input type="checkbox" name="billable" value="true" {{ 'checked' if field.billable }}/>
           </div>
           {% endif %}

           {% if field.input == "yesno" or field.input == "number" or field.input == "label" or field.input == "checkbox" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'price' %}</label>
                <input type="number" min=0 name="price" class="input-xlarge" id="input01" size="20" value="{{ any(field.price,'') }}">
                {% if (field.input == "number" ) %}
                    <span>{% _ "(price multiplied with entered number)" %}</span>
                {% endif %}
           </div>
           {% endif %}

           {% if field.input == "radio" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'default item' %}</label>
                <select id="defaultItem" name="defaultItem" >
                    <option value="">{% _ 'none' %}</option>
                    {% for el in field.values.radioitems %}
                        <option value="{{ el.caption }}" {{ "SELECTED" if field.values.defaultItem == el.caption }}>
                            {{ el.caption }}
                        </option>
                    {% endfor %}
                </select>
                 <span>{% _ "(Only available for input type : drop down menu)" %}</span>
           </div>
           {% endif %}

           {% if field.input == "radio" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'input type' %}</label>
                <select id="inputType" name="inputType" >
                    <option value="dropdown" {{ "SELECTED" if field.values.inputType == 'dropdown' }}>
                        {% _ 'drop down menu' %}
                    </option>
                    <option value="radiogroup" {{ "SELECTED" if field.values.inputType == 'radiogroup' }}>
                        {% _ 'radio group' %}
                    </option>
                </select>
           </div>
           {% endif %}

           {% if field.input == "date" %}
           <div class="regFormEditLine">
                <label class="regFormDialogCaption">{% _ 'Date format' %}</label>
                <select id="dateFormat" name="dateFormat" >
                    {% if _.isEmpty(field.values.displayFormats) %}
                        <option value="%d/%m/%Y %H:%M" selected="selected">DD/MM/YYYY hh:mm</option>
                        <option value="%d.%m.%Y %H:%M">DD.MM.YYYY hh:mm</option>
                        <option value="%m/%d/%Y %H:%M">MM/DD/YYYY hh:mm</option>
                        <option value="%m.%d.%Y %H:%M">MM.DD.YYYY hh:mm</option>
                        <option value="%Y/%m/%d %H:%M">YYYY/MM/DD hh:mm</option>
                        <option value="%Y.%m.%d %H:%M">YYYY.MM.DD hh:mm</option>
                        <option value="%d/%m/%Y">DD/MM/YYYY</option>
                        <option value="%d.%m.%Y">DD.MM.YYYY</option>
                        <option value="%m/%d/%Y">MM/DD/YYYY</option>
                        <option value="%m.%d.%Y">MM.DD.YYYY</option>
                        <option value="%Y/%m/%d">YYYY/MM/DD</option>
                        <option value="%Y.%m.%d">YYYY.MM.DD</option>
                        <option value="%m/%Y">MM/YYYY</option>
                        <option value="%m.%Y">MM.YYYY</option>
                        <option value="%Y">YYYY</option>
                     {% else %}
                        {% for el in field.values.displayFormats %}
                            <option value="{{ el[0] }}" {{ "SELECTED" if el[0] == field.values.dateFormat }}>
                                {{ el[1] }}
                            </option>
                        {% endfor %}
                     {% endif %}
                </select>
           </div>
           {% endif %}
            <input type="submit" style="display:none;" value="submit" id="form-opt-validate">
           </form>
        </div>
        <div class="tab-pane" id="div-editItems">
            <button id="addButton" class="addItem">{% _ 'Create new item' %}</button>
            <button id="sortItem"  class="sortItem">{% _ 'Sort alphabetically' %}</button>
            <div id="editionTable" style="margin-right:20px;margin-top:20px;"></div>
        </div>
    </div>
</div>
