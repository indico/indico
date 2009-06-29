<li class="UIGroup">
<span class="nameLink">
<% if selectable: %>
<input type="%(type)s" name="selectedPrincipals" value="%(id)s" %(selected)s>
<% end %>
%(fullName)s</span>

<% if not selectable: %>
<input 	type="image" class="UIRowButton"
			onclick="javascript:removeItem(<%= id %>, this.form);return false;"
			title="<%= _("Remove this person from the list")%>"
			src="<%= systemIcon("remove") %>" />	
<% end %>
</li>
