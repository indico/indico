<br />
<br />

<% backUrl =str(urlHandlers.UHAdminPlugins.getURL(PluginType, subtab = InitialPlugin)) %>
<a href="${ backUrl }">
    &lt;&lt; ${ _("Go back to ") + PluginType.getName() + _(" plugins administration") }
</a>

<div class="groupTitle">
    ${ _("Result of action ") + '"' + ActionName + '"' }:
</div>

${ ActionResult }
