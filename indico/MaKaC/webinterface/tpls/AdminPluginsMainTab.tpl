<form action="<%= urlHandlers.UHAdminPluginsSaveOptionReloadAll.getURL()%>" method="post">

    <% if PluginsHolder.getGlobalPluginOptions().getReloadAllWhenViewingAdminTab(): %>
        <% checked = "checked" %>
    <% end %>
    <% else: %>
        <% checked = "" %>
    <% end %> 
    
    <input type="checkbox" name="optionReloadAll" id="reloadAllCheckbox" <%= checked %> />
    <label for="reloadAllCheckbox"><%= _("Reload all plugins every time you open / navigate the Server Admin > Plugins tab")%></label>
    
    <input type="submit" value="<%= _("Save")%>" />

</form>


<form action="<%= urlHandlers.UHAdminPluginsReloadAll.getURL()%>" method="post">

    <input type="submit" value="<%= _("Reload All Manually")%>" /> <%= _("Press this button to manually reload all the plugins.")%>

</form>


<form action="<%= urlHandlers.UHAdminPluginsClearAllInfo.getURL()%>" method="post">

    <input type="submit" value="<%= _("Clear all info in DB")%>" /> <%= _("Press this button to clear all the information about plugins in the DB.")%>
    <span style="color:red;"><%= _("Warning: you will lose information about which plugins are active or not, option values, etc.")%></span>

</form>