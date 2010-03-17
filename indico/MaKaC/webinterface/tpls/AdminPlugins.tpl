<% declareTemplate(newTemplateStyle=True) %>
<% pluginList = PluginType.getPluginList(sorted = True, includeNonPresent = False, includeNonActive = True) %>

<table style="width: 100%%">
    <tr>
        <td class="groupTitle" colspan="3">
            <%= _("Active plugins for ") + PluginType.getName() %>
        </td>
    </tr>
    <tr>
        <td colspan="3">
            <span><%= PluginType.getDescription() %></span>
        </td>
    </tr>
    <tr>
        <td style="vertical-align:middle;white-space: nowrap;">
            <img src="<%=Config.getInstance().getSystemIconURL( 'enabledSection' )%>" alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled plugin")%></small>
            <br />
            <img src="<%=Config.getInstance().getSystemIconURL( 'disabledSection' )%>" alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled plugin")%></small>
            <br />
            <br />
            <form method="post" action="<%= urlHandlers.UHAdminReloadPlugins.getURL(PluginType) %>">
                <input type="submit" value="<%= _("Reload")%>"/>
            </form>
        </td>
        <td bgcolor="white" width="100%%" class="blacktext" style="padding-left:20px;vertical-align: top">
            <% if PluginType.hasPlugins() : %>
            <table align="left">
                <% for plugin in pluginList: %>
                <tr>
                    <td>
                        <% if plugin.isActive(): %>
                            <a href="<%=urlHandlers.UHAdminTogglePlugin.getURL(plugin)%>">
                                <img class="imglink" alt="<%= _("Click to disable")%>" src="<%=Config.getInstance().getSystemIconURL( 'enabledSection' )%>"/>
                            </a>
                        <% end %>
                        <% else: %>
                            <a href="<%=urlHandlers.UHAdminTogglePlugin.getURL(plugin)%>">
                                <img class="imglink" alt="<%= _("Click to enable")%>" src="<%=Config.getInstance().getSystemIconURL( 'disabledSection' )%>"/>
                            </a>
                        <% end %>
                        <a href="<%=urlHandlers.UHAdminTogglePlugin.getURL(plugin)%>">
                            <%= plugin.getName() %>
                        </a>
                        <% if plugin.hasDescription(): %>
                            <span style="margin-left: 2em;">
                                (<%= plugin.getDescription() %>)
                            </span>
                        <% end %>
                    </td>
                </tr>
                <% end %>
            </table>
            <% end %>
            <% else: %>
                <%= _("No plugins for ") + PluginType.getName() %>
            <% end %>
        </td>
    </tr>
</table>

<table style="width: 100%%; margin-top: 2em;">
    <tr>
        <td class="groupTitle" colspan="3">
            <%= _("Global settings for ") + PluginType.getName() %>
        </td>
    </tr>
    <% if PluginType.getOptions() is not None and len(PluginType.getOptions()) > 0: %>
        <% includeTpl('AdminPluginsOptionList', Object = PluginType, ObjectType = "PluginType", Favorites = Favorites, Index = 0) %>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <span><%= _("No global options defined for all ") + PluginType.getName() + _(" plugins")%></span>
        </td>
    </tr>
    <% end %>
</table>

<% if PluginType.hasPlugins() : %>
    <div class="groupTitle" style="width: 100%%; margin-top: 2em;">
        <%= _("Settings for individual plugins") %>
    </div>
    <div id="pluginTabs">
    </div>
    
    <div>
        <% for i, plugin in enumerate(pluginList): %>
        <div id="<%=plugin.getName()%>OptionsDiv" style="display:none;">
            <% if plugin.hasAnyOptions(): %>
                <% includeTpl('AdminPluginsOptionList', Object = plugin, ObjectType = "Plugin", Favorites = Favorites, Index = i) %>
            <% end %>
            <% else: %>
                <span><%=_("No options defined for this plugin")%></span>
            <% end %>
        </div>
        <% end %>
    </div>
    
<% end %>

<script type="text/javascript">
var tabList = [
    <%= ",\n".join(['["' + plugin.getName() + '" , $E("' + plugin.getName() + 'OptionsDiv")]' for plugin in pluginList])%>
]
var tabControl = new TabWidget(tabList, null, null, tabList[<%= InitialPlugin %>][0]);
$E('pluginTabs').set(tabControl.draw());

</script>