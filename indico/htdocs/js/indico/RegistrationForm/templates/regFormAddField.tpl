<div align="center" class="regFormAddField">
    <% _.each(fields, function(field){ %>
    <div id="<%= field.id %>" class="regFormAddFieldEntry" style="display:inline-block;">
        <div class="regFormAddFielIcon" style="clear:both;">
            <img src="<%= field.url %>">

        </div>
        <div style=" color: #555; clear:both; font-size:10px;"><%= field.desc %></div>
    </div>
    <% }); %>
</div>