<div>
    <% _.each(fields, function(field){ %>
    <div data-field-type="<%= field.id %>" class="regFormAddFieldEntry" style="display:inline-block;">
      <img class="icon" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" />
      <div class="icon_desc"><%= field.desc %></div>
    </div>
    <% }); %>
</div>