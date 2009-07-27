<div style="display:inline;" class="<%= DivClassName +str(Level) %>">
<% if len(DictObject) > 0: %> 
<ul class="<%= UlClassName +str(Level) %>">
<% for key, value in DictObject.items(): %>
    <li class="<%= LiClassName + str(Level) %>">
        <span class="<%= KeyClassName + str(Level)%>"><%= str(key) %></span> : <%= beautify(value, {"DivClassName": DivClassName, "UlClassName":UlClassName, "LiClassName":LiClassName, "KeyClassName":KeyClassName}, Level) %>
    </li>
<% end %>
</ul>
<% end %>
<% else: %>
<%= _("(Empty)")%>
<% end %>
</div>