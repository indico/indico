
<% for i in range(0, singleBookingPluginCount): %>
    <% if i > 0: %>
    <div class="horizontalLine" style="margin-top:1em;margin-bottom:1em;"></div>
    <% end %>
    
    <% plugin = SingleBookingPlugins[i] %>
    <% pluginId = plugin.getId() %>

    <% if allPluginCount > 1: %>
        <span class="titleCellFormat"><%= plugin.getDescription() %></span>
        <div id="<%=pluginId%>showHide" style="display:inline"></div>
        <% initialDisplay = "none" %>
    <% end %>
    <% else: %>
        <% initialDisplay = "block" %>
    <% end %>

    <div id="<%=pluginId%>Div" style="display:<%=initialDisplay%>;">
        <div id="<%=pluginId%>Info"></div>
        <div id="<%=pluginId%>Form" style="margin-top: 2em;">
        <%= SingleBookingForms[pluginId] %>
        </div>
    </div>
    
<% end %>

<script type="text/javascript">

var singlePluginNames = <%= str([plugin.getId() for plugin in SingleBookingPlugins]) %>
var singleBookings = {
    <%= ",\n". join(['"' + str(name) + '" \x3a ' + jsonEncode(booking).replace('%','%%') for name, booking in BookingsS.items()]) %>
}

var send = function(pluginId) {
    sendRequest(pluginId, '<%= Conference.getId() %>');
}

var withdraw = function(pluginId) {
    withdrawRequest(pluginId, '<%= Conference.getId() %>');
}

/* ------------------------------ STUFF THAT HAPPENS WHEN PAGE IS LOADED -------------------------------*/

<% if allPluginCount > 1: %>
IndicoUI.executeOnLoad(function() {
    <% for plugin in SingleBookingPlugins: %>
    buildShowHideButton("<%= pluginId %>");
    <% end %>
});
<% end %>

IndicoUI.executeOnLoad(function(){

<% if SingleBookingPlugins: %>
    <% for plugin in SingleBookingPlugins: %>
    if (pluginHasFunction("<%= pluginId %>", "onLoad")) {
        codes["<%= pluginId %>"]["onLoad"]();
    }
    <% end %>
<% end %>

loadBookings();
});

</script>