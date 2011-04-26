
% for i in range(0, len(SingleBookingPlugins)):
    % if i > 0:
    <div class="horizontalLine" style="margin-top:1em;margin-bottom:1em;"></div>
    % endif

    <% plugin = SingleBookingPlugins[i] %>
    <% pluginId = plugin.getId() %>

    % if len(SingleBookingPlugins) + len(MultipleBookingPlugins) > 1:
        <span class="titleCellFormat">${ plugin.getDescription() }</span>
        <div id="${pluginId}showHide" style="display:inline"></div>
        <% initialDisplay = "none" %>
    % else:
        <% initialDisplay = "block" %>
    % endif

    <div id="${pluginId}Div" style="display:${initialDisplay};">
        <div id="${pluginId}Info"></div>
        <div id="${pluginId}Form" style="margin-top: 2em;">
        ${ SingleBookingForms[pluginId] }
        </div>
    </div>

% endfor

<script type="text/javascript">

var singlePluginNames = ${ str([plugin.getId() for plugin in SingleBookingPlugins]) }
var singleBookings = {
    ${ ",\n". join(['"' + str(name) + '" \x3a ' + jsonEncode(booking).replace('%','%%') for name, booking in BookingsS.items()]) }
}

var send = function(pluginId) {
    sendRequest(pluginId, '${ Conference.getId() }');
}

var withdraw = function(pluginId) {
    withdrawRequest(pluginId, '${ Conference.getId() }');
}

/* ------------------------------ STUFF THAT HAPPENS WHEN PAGE IS LOADED -------------------------------*/

% if len(SingleBookingPlugins) + len(MultipleBookingPlugins) > 1:
IndicoUI.executeOnLoad(function() {
    % for plugin in SingleBookingPlugins:
    buildShowHideButton("${ pluginId }");
    % endfor
});
% endif

IndicoUI.executeOnLoad(function(){

% if SingleBookingPlugins:
    % for plugin in SingleBookingPlugins:
    if (pluginHasFunction("${ pluginId }", "onLoad")) {
        codes["${ pluginId }"]["onLoad"]();
    }
    % endfor
% endif

loadBookings();
});

</script>
