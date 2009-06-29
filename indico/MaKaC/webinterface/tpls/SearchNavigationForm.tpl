<% if direction == 'Next': %>
  <% inc = 1 %>
<% end %>
<% else: %>
  <% inc = -1 %>
<% end %>

<% if target == 'Events': %>
  <% resList = eventResults %>
<% end %>
<% else: %>
  <% resList =  contribResults %>
<% end %>


<form id="<%= direction %>Form<%= target %>" method="GET" action="<%= urlHandlers.UHSearch.getURL()%>">
  <input type="hidden" name="startDate" value="<%= startDate %>"/>
  <input type="hidden" name="endDate" value="<%= endDate %>"/>
  <input type="hidden" name="p" value="<%= p %>"/>
  <input type="hidden" name="f" value="<%= f %>"/>
  <input type="hidden" name="collections" value="<%= target %>"/>
  <% if type(self._rh._target) == MaKaC.conference.Category: %>
    <input type="hidden" name="categId" value="<%= self._rh._target.getId() %>" />
  <% end %>
  <% elif type(self._rh._target) == MaKaC.conference.Conference: %>
    <input type="hidden" name="confId" value="<%= self._rh._target.getId() %>" />
  <% end %>
  <% if len(resList) > 0: %>
    <input type="hidden" name="page" value="<%= page + inc %>" />
  <% end %>
    <input type="hidden" name="sortOrder" value="<%= sortOrder %>" />
</form>