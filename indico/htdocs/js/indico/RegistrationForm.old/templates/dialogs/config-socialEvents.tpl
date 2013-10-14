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
