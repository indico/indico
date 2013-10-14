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
