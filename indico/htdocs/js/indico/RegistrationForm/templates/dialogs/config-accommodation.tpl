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
