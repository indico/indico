<% if material: %>\
    <div>
		<%= material %>
	</div>
<% end %>

<ul class="list">
<% for item in items: %>
	<% includeTpl('CategoryListItem', lItem=item, categoryDisplayURLGen=categoryDisplayURLGen) %>
<% end %>
</ul>
