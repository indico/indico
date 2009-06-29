<h2>OAI Private Harvesters</h2>
<% if addedIP: %>
  IP Address '<%= addedIP %>' was added!
<% end %>
<% if len(ipList) == 0: %>
  <em>None - you can add one using the form below</em>
<% end %>
<% else: %>
  <ul style="display: block; width: 150px;">
    <% for ip in ipList: %>
      <li style="display: block; height:20px;">
	<div style="float: left;"><%= ip %></div>
	   <form action="<%= urlHandlers.UHOAIPrivateConfigRemoveIP.getURL() %>" method="POST" style="display:inline;">
	     <input type="image" class="UIRowButton" onclick="this.form.submit();return false;" title="Remove this IP from the list" src="<%= systemIcon("remove") %>" style="float: right;"/>
	     <input type="hidden" name="ipAddress" value="<%= ip %>" />
	   </form>
      </li>
    <% end %>
  </ul>
<% end %>
<div style="margin-top: 20px;">
<form action="<%= urlHandlers.UHOAIPrivateConfigAddIP.getURL() %>" method="POST">
<label>IP Address:</label><input type="text" name="ipAddress" />
<input type="Submit" value="Add"/>
</form>
</div>
