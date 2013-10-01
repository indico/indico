<script type="text/template" id="edit-dialog">
<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        {% for tab in section.tabs %}
            <li>
                <a data-toggle="tab" id="tab-{{ tab.id }}" ref="#div-{{ tab.id }}">{{ tab.name }}</a>
            </li>
        {% endfor %}
    </ul>
    <div class="tab-content regFormDialogTabContent" style="width: {{ contentWidth }}px; overflow: hidden; white-space: nowrap;">
        {% for tab in section.tabs %}
            <div class="tab-pane" id="div-{{ tab.id }}">
                {{ getTabHtml(tab) }}
            </div>
        {% endfor %}
    </div>
</div>
</script>

<script type="text/template" id="config-socialEvents">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption">{% _ 'Selection type' %}</label>
        <select name="selectionType">
            <option value="unique" {{"selected" if selectionType == "unique" }}>
                {% _ 'Unique choice' %}
            </option>
            <option value="multiple" {{"selected" if selectionType == "multiple" }}>
                {% _ 'Multiple choice' %}
            </option>
        </select>
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption">{% _ 'Introduction sentence' %}</label>
        <textarea id="descriptionEdit" name="introSentence" cols="40" rows="6">{{ introSentence }}</textarea>
     </div>
</form>
</script>

<script type="text/template" id="config-sessions">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption" style="width : 180px">{% _ "Type of sessions' form" %}</label>
        <select name="type">
            <option value="2priorities" {{ "selected" if type == "2priorities" }}>
                {% _ '2 choices' %}
            </option>
            <option value="all" {{ "selected" if type == "all" }}>{% _ 'multiple' %}</option>
        </select>
    </div>
    <span> {% _ 'How many sessions the registrant can choose.' %}
        <br> {% _ 'Please note that billing is not possible when using 2 choices' %}
    </span>
</form>
</script>

<script type="text/template" id="addSession-sessions">
<form>
    {% for el in sessions %}
        <input type="checkbox" name="session" value="{{ el.id }}">{{ el.caption }}</input>
    {% endfor %}
</form>
</script>

<script type="text/template" id="editionTable-sessions">
<div id="editionTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="editionTable-socialEvents">
<div class="regFormEditLine" style="margin-bottom: 20px;">
    <button id="addButton" class="addItem">{% _ 'Add a new social event' %}</button>
</div>
<div id="editionConfigTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="editionTable-accommodation">
<div class="regFormEditLine" style="margin-bottom: 20px;">
    <button id="addButton" class="addItem">{% _ 'Add a new accommodation' %}</button>
</div>
<div id="editionTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="cancelEvent-socialEvents">
    <div id="editionCanceledTable" class="regFormDialogEditionTable"></div>
</script>

<script type="text/template" id="cancelEvent-socialEventsOLD">
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine">{% _ 'Cancellation of the "{0}" social event').format('<span id="cancelEventCaption"></span>' %}</label>
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption">{% _ 'Reason' %}</label>
         <textarea id="cancelledReason" cols="40" rows="6"></textarea>
    </div>
    <div class="regFormEditLine" style="margin-bottom: 20px;">
        <button id="cancelEvent">{% _ 'Cancel Event' %}</button>
        <button id="undoCancelEvent">{% _ 'Undo' %}</button>
    </div>
</script>

<script type="text/template" id="config-accommodation">
<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine">{% _ 'Arrival dates (offset)' %}</label>
        {% _ 'event start date offset:' %}
        <input type="text" name="aoffset1" size="2" value="{{ arrivalOffsetDates[0] }}"/>
        {% _ 'days' %}-&gt;
        {% _ 'event end date offset:' %}
        <input type="text" name="aoffset2" size="2" value="{{ arrivalOffsetDates[1] }}">
        {% _ 'days' %}
    </div>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaptionLine">{% _ 'Departure dates (offset)' %}</label>
        {% _ 'event start date offset:' %}
        <input type="text" name="doffset1" size="2" value="{{ departureOffsetDates[0] }}">
        {% _ 'days' %} -&gt;
        {% _ 'event end date offset:' %}
        <input type="text" name="doffset2" size="2" value="{{ departureOffsetDates[1] }}">
        {% _ 'days' %}
    </div>
</form>
</script>

