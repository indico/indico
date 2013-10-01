<script type="text/template" id="section">
<div id="{{ section.id }}" class="regFormSectionMgmt">
    <div class="regFormHeaderMgmt">
        <div class="regFormSectionTitle">{{ section.title }}
        {% if section.create %}
            <div style="float:right; font-size:14px;">
                <button id="buttonCreate" class="regFormButton">{% _ 'Create' %}</button>
            </div>
        {% else %}
            <div style="float:right; font-size:14px;">
                <button id="buttonRestore" class="regFormButton">{% _ 'Restore' %}</button>
                {% if parseInt(section.id) > 0 %}
                <button id="buttonRemove" class="regFormButton">{% _ 'Remove' %}</button>
                {% endif %}
            </div>
        {% endif %}
        </div>
    </div>
</div>
</script>

<script type="text/template" id="section-create">
<form id="newSectionForm">
    <div class="regFormSectionNewSection">
        <input type="text" name="title" size="50px" class="regFormTitleInputMgmt" placeholder="{% _ 'new section name' %}" required>
        <textarea  name="description" rows="4" cols="50px" class="regFormDescriptionInputMgmt" placeholder="{% _ 'Description' %}"></textarea>
    </div>
</form>
</script>

<script type="text/template" id="infos">
<div class="regFormInfoMessage"></div>
</script>


<script type="text/template" id="message">
    {{ message }}
</script>
