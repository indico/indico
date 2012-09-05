<script type="text/template" id="editionInputInlineForm">
    <form action="#" id="tmpEditionForm">
        <% if (data.itemType == "title") { %>
            <input type="text" name="<%= data.itemType %>" size="40" class="regFormInlineEdition" value="<%= data.text %>"/>
        <% } else { %>
            <textarea name="<%= data.itemType %>" rows="4" cols="80" class="regFormInlineEdition"><%= data.text %></textarea>
        <% } %>
        <input type="hidden" name="sectionId" value="<%= data.sectionId %>" />
    </form>
</script>

<script type="text/template" id="sectionButtons">
    <div style="float:right;">
        <% if (actions.indexOf("addField") > -1) { %>
        <button class="buttonAddField regFormButtonAdd"><%= $T('Click to add a field to this section') %></button>
        <% } if (actions.indexOf("settings") > -1) { %>
        <button id="buttonEditSection" class="regFormButtonEdition"><%= $T('Edit this section') %></button>
        <% } if (actions.indexOf("disable") > -1) { %>
        <button id="buttonDisableSection" class="regFormButtonTrash"><%= $T('Click to disable this section') %></button>
        <% } %>
        <button id="buttonCollpaseSection" class="regFormButtonCollpase"><%= $T('Click to toggle collapse status') %></button>
    </div>
</script>

<script type="text/template" id="fieldButtons">
    <div id="itemEdition" class="regFormFloatRight" >
        <% if (locks.indexOf("disable") == -1) { %>
        <button id="buttonFieldDisable" class="regFormButtonDisable"><%= $T('Disable this field') %></button>
        <% } %>
        <% if (locks.indexOf("delete") == -1) { %>
        <button id="buttonFieldRemove" class="regFormButtonRemove"><%= $T('Remove this field') %></button>
        <% } %>
        <button id="buttonFieldEdit" class="regFormButtonEdition"><%= $T('Edit this field') %></button>
    </div>
</script>

<script type="text/template" id="fieldDisabledButtons">
    <div id="itemEdition" class="regFormFloatRight" >
        <button id="buttonFieldEnable" class="regFormButtonEnable"><%= $T('Enabled this field') %></button>
    </div>
</script>

<script type="text/template" id="disabledFields">
    <% for (var j = 0; j < section.items.length; j++) { %>
        <% var field = section.items[j]; %>
        <% if ( field.disabled ) { %>
            <%= fields.render(field, section.id) %>
        <% } %>
    <% } %>
</script>



