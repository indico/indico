<% pluginList = PluginType.getPluginList(doSort = True, includeNonPresent = False, includeNonActive = True) %>

<table style="width: 100%">
    <tr>
        <td class="groupTitle" colspan="3">
            ${ _("Active plugins for ") + PluginType.getName() }
        </td>
    </tr>
    <tr>
        <td colspan="3">
            <span>${ PluginType.getDescription() }</span>
        </td>
    </tr>
    <tr>
        <td style="vertical-align:middle;white-space: nowrap;">
            <img src="${Config.getInstance().getSystemIconURL( 'enabledSection' )}" alt="${ _("Click to disable")}"> <small> ${ _("Enabled plugin")}</small>
            <br />
            <img src="${Config.getInstance().getSystemIconURL( 'disabledSection' )}" alt="${ _("Click to enable")}"> <small> ${ _("Disabled plugin")}</small>
            <br />
            <br />
            <form method="post" action="${ urlHandlers.UHAdminReloadPlugins.getURL(PluginType) }">
                <input type="submit" value="${ _("Reload")}"/>
            </form>
        </td>
        <td bgcolor="white" width="100%" class="blacktext" style="padding-left:20px;vertical-align: top">
            % if PluginType.hasPlugins() :
            <table align="left">
                % for plugin in pluginList:
                <tr>
                    <td>
                        % if not plugin.isUsable():
                            <img class="imglink" alt="${ _("Not in usable state")}" src="${Config.getInstance().getSystemIconURL( 'greyedOutSection' )}"/>
                        % elif plugin.isActive():
                            <a href="${urlHandlers.UHAdminTogglePlugin.getURL(plugin)}">
                                <img class="imglink" alt="${ _("Click to disable")}" src="${Config.getInstance().getSystemIconURL( 'enabledSection' )}"/>

                            </a>
                        % else:
                            <a href="${urlHandlers.UHAdminTogglePlugin.getURL(plugin)}">
                                <img class="imglink" alt="${ _("Click to enable")}" src="${Config.getInstance().getSystemIconURL( 'disabledSection' )}"/>
                            </a>
                        % endif
                        % if not plugin.isUsable():
                            ${ plugin.getName() }
                            <small class="smallRed">
                                (${ plugin.getNotUsableReason() })
                            </small>
                        % else:
                        <a href="${urlHandlers.UHAdminTogglePlugin.getURL(plugin)}">
                            ${ plugin.getName() }
                        </a>
                        % endif
                        % if plugin.hasDescription():
                            <span style="margin-left: 2em;">
                                (${ plugin.getDescription() })
                            </span>
                        % endif
                    </td>
                </tr>
                % endfor
            </table>
            % else:
                ${ _("No plugins for ") + PluginType.getName() }
            % endif
        </td>
    </tr>
</table>

<table style="width: 100%; margin-top: 2em;">
    <tr>
        <td class="groupTitle" colspan="3">
            ${ _("Global settings for ") + PluginType.getName() }
        </td>
    </tr>
    % if True in self_._notify('hasPluginSettings', PluginType.getId(), None):
    <tr>
        <td>
                ${ ''.join(list(elem for elem in self_._notify('getPluginSettingsHTML', PluginType.getId(), None) if elem != None)) }
        </td>
    </tr>
    % endif
    % if PluginType.getOptions() is not None and len(PluginType.getOptions()) > 0:
         <%include file="AdminPluginsOptionList.tpl" args="Object = PluginType, ObjectType = 'PluginType', Favorites = Favorites, Index = 0, rbActive = rbActive, baseURL = baseURL"/>
    % endif
    % if not PluginType.getOptions() and True not in self_._notify('hasPluginSettings', PluginType.getId(), None):
    <tr>
        <td>
            <span>${ _("No global options defined for all ") + PluginType.getName() + _(" plugins")}</span>
        </td>
    </tr>
    % endif
</table>

% if PluginType.hasPlugins() :
    <div class="groupTitle" style="width: 100%; margin-top: 2em;">
        ${ _("Settings for individual plugins") }
    </div>
    <div id="pluginTabs">
    </div>

    <div>
        % for i, plugin in enumerate(pluginList):
        <div id="${plugin.getName()}OptionsDiv" style="display:none;">
            % if plugin.hasAnyOptions():
                <%include file="AdminPluginsOptionList.tpl" args="Object = plugin, ObjectType = 'Plugin', Favorites = Favorites, Index = i, rbActive = rbActive, baseURL = baseURL"/>
            % elif True in self_._notify('hasPluginSettings', PluginType.getId(), plugin.getId()):
                ${ ''.join(list(elem for elem in self_._notify('getPluginSettingsHTML', PluginType.getId(), plugin.getId()) if elem != None)) }
            % else:
                <span>${_("No options defined for this plugin")}</span>
            % endif
        </div>
        % endfor
    </div>

% endif

<script type="text/javascript">
var tabList = [
    ${ ",\n".join(['["' + plugin.getName() + '" , $E("' + plugin.getName() + 'OptionsDiv")]' for plugin in pluginList])}
]
var tabControl = new JTabWidget(tabList, null, null, ${ InitialPlugin });
$('#pluginTabs').html(tabControl.draw());

</script>
