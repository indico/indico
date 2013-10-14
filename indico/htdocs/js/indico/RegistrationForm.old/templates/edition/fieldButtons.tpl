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
