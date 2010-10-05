<% declareTemplate(newTemplateStyle=True) %>

<table width="100%" align="center" border="0" cellpadding="5px">
    <tr>
        <td colspan="10" class="groupTitle"> <%= _("Chat rooms for ")%> <%= Conference.getTitle()%></td>
    </tr>

	    <tr>
			<td></td>
	        <td nowrap class="titleChat"> <%= _("Room")%></td>
	        <td nowrap class="titleChat"> <%= _("Server")%></td>
	        <td nowrap class="titleChat"> <%= _("Description")%></td>
	        <td nowrap class="titleChat"> <%= _("Requires password")%></td>
	        <td nowrap class="titleChat"> <%= _("Password")%></td>
	    </tr>

    	<% for cr in Chatrooms: %>
    		<% if cr.getCreateRoom():%>
    			<% server = 'conference.' + cr.getHost() %>
    		<% end %>
    		<% else:%>
    			<% server = cr.getHost() %>
    		<% end %>

		    <tr style="vertical-align: baseline;">
				<td></td>
		        <td> <a href="xmpp:<%= cr.getTitle()%>@<%= server%>?join" ><%= cr.getTitle()%></td>

	        	<td style="font-family:monospace;"> <%= server%></td>

		        <td style="width:200px"><div id='desc<%= cr.getId() %>'> <%= cr.getDescription()%></div></td>

		        <td> <%= _('Yes') if len(cr.getPassword()) > 0 else _('No')%></td>

		        <% if cr.getShowPass() and len(cr.getPassword()) > 0:%>
		        	<td> <%= cr.getPassword()%> </td>
   	 			<% end %>
		        <% elif not cr.getShowPass() and len(cr.getPassword()) > 0:%>
		        	<td style="font-style:italic"> <%= _('Not displayed')%> </td>
   	 			<% end %>
   	 			<% else:%>
		        	<td style="font-style:italic"> - </td>
   	 			<% end %>
		    </tr>
   	 	<% end %>
</table>


<table width="100%" align="center" border="0">
    <tr>
        <td class="groupTitle" style="padding-top:50px"><%= _("How to connect to the chat")%></td>
    </tr>
    <tr>
      	<td>
      	    <ul>
      			<li><%= _("Download a messaging client compatible with XMPP (like Pidgin, Gajim, Adium, Spark...You may want to look") %> <a href=http://xmpp.org/software/clients.shtml> <%= _("here") %></a>) <%=_("and install it.")%></li>
				<li><%= _("Add the Jabber account that you want to use.")%></li>
				<li><%= _("In the menus, try to find something like 'Join a Chat', 'Join Group Chat', or related.")%></li>
				<li><%= _("Fill the fields Room and Server with the information above. In case there is only one field for both the room and the server, the format to use is 'room@server'.")%></li>
			</ul>
		</td>
	</tr>
</table>
