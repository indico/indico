
<% for i in range(0, singleBookingPluginCount): %>
    <% if i > 0: %>
    <div class="horizontalLine" style="margin-top:1em;margin-bottom:1em;"></div>
    <% end %>
    
    <% plugin = SingleBookingPlugins[i] %>
    <% pluginName = plugin.getName() %>

    <% if allPluginCount > 1: %>
        <span class="titleCellFormat"><%= plugin.getDescription() %></span>
        <div id="<%=pluginName%>showHide" style="display:inline"></div>
        <% initialDisplay = "none" %>
    <% end %>
    <% else: %>
        <% initialDisplay = "block" %>
    <% end %>

    <div id="<%=pluginName%>Div" style="display:<%=initialDisplay%>;">
        <div id="<%=pluginName%>Info"></div>
        <div id="<%=pluginName%>Form" style="margin-top: 2em;">
        <%= SingleBookingForms[pluginName] %>
        </div>
    </div>
    
<% end %>

<script type="text/javascript">

var singlePluginNames = <%= str([plugin.getName() for plugin in SingleBookingPlugins]) %>
var singleBookings = {
    <%= ",\n". join(['"' + str(name) + '" \x3a ' + jsonEncode(booking).replace('%','%%') for name, booking in BookingsS.items()]) %>
}

var send = function(pluginName) {
    sendRequest(pluginName, '<%= Conference.getId() %>');
}

var withdraw = function(pluginName) {
    withdrawRequest(pluginName, '<%= Conference.getId() %>');
}

/* ------------------------------ STUFF THAT HAPPENS WHEN PAGE IS LOADED -------------------------------*/

<% if allPluginCount > 1: %>
IndicoUI.executeOnLoad(function() {
    <% for plugin in SingleBookingPlugins: %>
    buildShowHideButton("<%= plugin.getName() %>");
    <% end %>
});
<% end %>

IndicoUI.executeOnLoad(loadBookings);

</script>