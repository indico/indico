<form action="#" id="tmpEditionForm">
    {% if data.itemType == "title" %}
        <input type="text" name="{{ data.itemType }}" size="40" class="regFormInlineEdition" value="{{ data.text }}"/>
    {% else %}
        <textarea name="{{ data.itemType }}" rows="4" cols="80" class="regFormInlineEdition">{{ data.text }}</textarea>
    {% endif %}
    <input type="hidden" name="sectionId" value="{{ data.sectionId }}" />
</form>
