<div style="display:inline;" class="<%= DivClassName + str(Level) %>">
<% if len(ListObject) > 0: %>
<ul class="<%= UlClassName +str(Level) %>">
<% for item in ListObject: %>
    <li class="<%= LiClassName + str(Level) %>">
        <%= beautify(item, {"DivClassName": DivClassName, "UlClassName":UlClassName, "LiClassName":LiClassName}, Level) %>
    </li>
<% end %>
</ul>
<% end %>
<% else: %>
<%= _("(Empty)")%>
<% end %>
</div>