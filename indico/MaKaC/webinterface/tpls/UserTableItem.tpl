<li class="UIPerson clearfix" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'" >

    <% if not selectable: %>
        <input  type="image" style="padding: 3px;" class="UIRowButton"
                onclick="javascript:removeItem(<%= id %>, this.form);return false;"
                title="<%= _("Remove this person from the list")%>"
                src="<%= systemIcon("remove") %>" />
    <% end %>

    <% if currentUserBasket: %>
        <% domId = id %>
        <% if ParentPrincipalTableId: %>
            <% domId = "t" + str(ParentPrincipalTableId) + "av" + id %>
        <% end %>

        <span id="add_<%= domId %>_to_basket" class="UIRowButton" style="padding: 3px; height: 16px;"></span>
        <script type="text/javascript">
            $E('add_<%= domId %>_to_basket').set(new FavouritizeButton(<%= jsonEncode(avatar) %>, {}, <%= jsBoolean(currentUserBasket.hasUserId(id)) %>).draw());
        </script>
    <% end %>


    <span class="nameLink">

        <% if selectable: %>
    	<input type="<%= inputType %>" name="selectedPrincipals" value="%(id)s" %(selected)s>
        <% end %>

        %(fullName)s <em>(%(email)s)</em>
    </span>

</li>
