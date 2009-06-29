<% if currentUser: %>
		<li><span><%= _("Logged in as")%></span><a href="<%= urlHandlers.UHUserDetails.getURL(currentUser) %>"><%= currentUser.getAbrName() %></a></li>
        <% if currentUser.isAdmin(): %>
            <li><a href="<%= loginAsURL %>"><%= _("Login as...") %></a></li>
        <% end %>
        <li style="border-right: none;"><a href="<%= logoutURL %>"><%= _("Logout") %></a></li>
<% end %>
<% else: %>
 	<li class="loginHighlighted" style="border-right: none;"><a href="<%= loginURL %>"><strong style="color: white"><%= _("Login")%></strong></a></li>
<% end %>
