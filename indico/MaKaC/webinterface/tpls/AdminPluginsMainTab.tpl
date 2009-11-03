<div style="padding-top: 1em;">
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
</div>

<div style="padding-top: 1em;">
<form action="<%= urlHandlers.UHAdminPluginsReloadAll.getURL()%>" method="post">
    <input type="submit" value="<%= _("Reload All Manually")%>" /> <%= _("Press this button to manually reload all the plugins.")%>
</form>
</div>

<!--
<form action="<%= urlHandlers.UHAdminPluginsClearAllInfo.getURL()%>" method="post">

    <input type="submit" value="<%= _("Clear all info in DB")%>" /> <%= _("Press this button to clear all the information about plugins in the DB.")%>
    <span style="color:red;"><%= _("Warning: you will lose information about which plugins are active or not, option values, etc.")%></span>

</form>
 -->

<% if PluginsHolder.getPluginTypes(includeNonVisible = False): %>
<table style="width: 100%%; padding-top: 2em;">
    <tr>
        <td class="groupTitle" colspan="3">
            <%= _("Active plugin types ") %>
        </td>
    </tr>
    <tr>
        <td style="vertical-align:middle;white-space: nowrap;">
            <img src="<%=Config.getInstance().getSystemIconURL( 'enabledSection' )%>" alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled plugin type")%></small>
            <br />
            <img src="<%=Config.getInstance().getSystemIconURL( 'disabledSection' )%>" alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled plugin type")%></small>
        </td>
        <td bgcolor="white" width="100%%" class="blacktext" style="padding-left:20px;vertical-align: top">
            <table align="left">
                <% for pluginType in PluginsHolder.getPluginTypes(includeNonVisible = False): %>
                <tr>
                    <td>
                        <a href="<%=urlHandlers.UHAdminTogglePluginType.getURL(pluginType)%>">
                        <% if pluginType.isActive(): %>
                                <img class="imglink" alt="<%= _("Click to disable")%>" src="<%=Config.getInstance().getSystemIconURL( 'enabledSection' )%>"/>
                        <% end %>
                        <% else: %>
                                <img class="imglink" alt="<%= _("Click to enable")%>" src="<%=Config.getInstance().getSystemIconURL( 'disabledSection' )%>"/>
                        <% end %>
                        </a>
                        <a href="<%=urlHandlers.UHAdminTogglePluginType.getURL(pluginType)%>">
                            <%= pluginType.getName() %>
                        </a>
                        <% if pluginType.hasDescription(): %>
                            <span style="margin-left: 2em;">
                                (<%= pluginType.getDescription() %>)
                            </span>
                        <% end %>
                    </td>
                </tr>
                <% end %>
            </table>
        </td>
    </tr>
</table>
<% end %>
<% else: %>
    <%= _("No plugin types in the system (or non marked as visible)") %>
<% end %>