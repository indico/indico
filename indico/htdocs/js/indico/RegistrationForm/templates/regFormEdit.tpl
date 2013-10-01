<script type="text/template" id="editionInputInlineForm">
    <form action="#" id="tmpEditionForm">
        {% if data.itemType == "title" %}
            <input type="text" name="{{ data.itemType }}" size="40" class="regFormInlineEdition" value="{{ data.text }}"/>
        {% else %}
            <textarea name="{{ data.itemType }}" rows="4" cols="80" class="regFormInlineEdition">{{ data.text }}</textarea>
        {% endif %}
        <input type="hidden" name="sectionId" value="{{ data.sectionId }}" />
    </form>
</script>

<script type="text/template" id="sectionButtons">
    <div class="toolbar">
        <div class="group right">
            {% if actions.indexOf("addField") > -1 %}
                <a class="buttonAddField i-button icon-plus" title="{% _ 'Click to add a field to this section' %}"></a>
            {% endif %}
            {% if actions.indexOf("settings") > -1 %}
                <a id="buttonEditSection" class="i-button icon-wrench" title="{% _ 'Edit this section' %}"></a>
            {% endif %}
            {% if actions.indexOf("disable") > -1 %}
                <a id="buttonDisableSection" class="i-button icon-disable" title="{% _ 'Click to disable this section' %}"></a>
            {% endif %}
            <a id="buttonCollpaseSection" class="i-button icon-prev" title="{% _ 'Click to toggle collapse status' %}"></a>
        </div>
    </div>
</script>

<script type="text/template" id="fieldButtons">
    <div id="itemEdition" class="toolbar regFormFloatRight">
        <div class="group right">
          {% if locks.indexOf("disable") == -1 %}
              <a id="buttonFieldDisable" class="i-button icon-disable" title="{% _ 'Click to disable this field' %}"></a>
          {% endif %}
          {% if locks.indexOf("delete") == -1 %}
              <a id="buttonFieldRemove" class="i-button icon-remove" title="{% _ 'Click to remove this field' %}"></a>
          {% endif %}
              <a id="buttonFieldEdit" class="i-button icon-wrench" title="{% _ 'Click to edit this field' %}"></a>
        </div>
    </div>
</script>

<script type="text/template" id="fieldDisabledButtons">
    <div id="itemEdition" class="toolbar regFormFloatRight">
        <div class="group right">
          <a id="buttonFieldEnable" class="i-button icon-checkmark" title="{% _ 'Click to enable this field' %}"></a>
        </div>
    </div>
</script>

<script type="text/template" id="disabledFields">
    {% for i in range(section.items.length) %}
        <% var field = section.items[i]; %>
        {% if field.disabled %}
            {{ fields.render(field, section.id) }}
        {% endif %}
    {% endfor %}
</script>



