<li>
      <span>
      	<% if lItem.getConferenceList() != []: %>            
      		<a style="display: none;" href="<%= urlHandlers.UHCategoryToiCal.getURL(lItem) %>"><img src="<%= systemIcon("ical") %>" alt="<%= _("iCal export")%>" /></a>
      	<% end %>
      </span>
      <span style="display: none;" class="list1stDeg">
      	<a href="<%= urlHandlers.UHCalendar.getURL([lItem]) %>"><img src="<%= systemIcon("year") %>" alt="<%= _("Calendar")%>" /></a>
      </span>
      <span style="display: none;" class="list2ndDeg">
      	<a href="<%= urlHandlers.UHCategoryOverview.getURL(lItem) %>"><img src="<%= systemIcon("day") %>" alt="<%= _("Overview")%>" /></a>
      </span>
      <span style="display: none;" class="list3rdDeg">
      	<a href="<%= urlHandlers.UHCategoryStatistics.getURL(lItem) %>"><img src="<%= systemIcon("stat") %>" alt="<%= _("Statistics")%>" /></a>
      </span>
      <span>
      	<a href="<%= categoryDisplayURLGen(lItem) %>"><%= escape(lItem.getName().strip()) or _("[no title]") %></a>
      	
        <em>(<%= lItem.getNumConferences() %>)</em>

		<% if lItem.hasAnyProtection(): %>
      		<span class="protected">
				<% if lItem.getDomainList() != []: %>
					<%= "%s domain only"%(", ".join(map(lambda x: x.getName(), lItem.getDomainList()))) %>
				<% end %>
				<% else: %>
					<%= _("(protected)")%>
				<% end %>
			</span>
		<% end %>
      </span>

</li>