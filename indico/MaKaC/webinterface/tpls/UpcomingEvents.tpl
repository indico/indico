<ul>
<% for (status, dateTime, eventTitle, eventId) in upcomingEvents: %>
<li>

  <a title="<%= escape(eventTitle) %>" href="<%= urlHandlers.UHConferenceDisplay.getURL(confId=eventId) %>"><%= truncateTitle(escape(eventTitle)) %></a>

  <% if status == 'ongoing': %>
    <em><%= _("ongoing till") %>&nbsp;<%= self.formatDateTime( dateTime ) %></em>
  <% end %>
  <% else: %>
    <em><%= _("starts") %>&nbsp;<%= self.formatDateTime( dateTime ) %></em>
  <% end %>

</li>
<% end %>
</ul>