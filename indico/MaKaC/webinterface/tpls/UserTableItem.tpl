<li class="UIPerson clearfix" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'" >

<% if not selectable: %>
    <input  type="image" style="padding: 3px;" class="UIRowButton"
            onclick="javascript:removeItem(<%= id %>, this.form);return false;"
            title="<%= _("Remove this person from the list")%>"
            src="<%= systemIcon("remove") %>" />    
<% end %>

<% if currentUserBasket: %>
    <span id="add_<%= id %>_to_basket" class="UIRowButton" style="padding: 3px; height: 16px;"></span>
    <script type="text/javascript">
        $E('add_<%= id %>_to_basket').set(new AddToFavoritesButton(<%= jsBoolean(currentUserBasket.hasUserId(id)) %>, '<%= id %>').draw());
    </script>
<% end %>


<span class="nameLink">
<% if selectable: %>
	<input type="%(type)s" name="selectedPrincipals" value="%(id)s" %(selected)s>
<% end %>
%(fullName)s <em>(%(email)s)</em></span>

</li>
