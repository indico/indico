<li>
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