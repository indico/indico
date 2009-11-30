<li class="UIPerson clearfix" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'" >

<% if not selectable: %>
    <input  type="image" style="padding: 3px;" class="UIRowButton"
            onclick="javascript:removeItem('<%= email %>', this.form);return false;"
            title="<%= _("Remove this person from the list")%>"
            src="<%= systemIcon("remove") %>" />    
<% end %>


<span class="nameLink">
<% if selectable: %>
	<input type="%(type)s" name="selectedPrincipals" value="%(email)s" %(selected)s>
<% end %>
Non-registered user <em>(%(email)s)</em></span>

</li>
