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
		        <td> <%= cr.getTitle()%> </td>

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
                <td><a href="xmpp:<%= cr.getTitle()%>@<%= server%>?join" >Join now!</td>
		    </tr>
   	 	<% end %>
</table>

<% from MaKaC.plugins.helpers import PluginFieldsHelper %>
<%= PluginFieldsHelper('InstantMessaging', 'Jabber').getOption('ckEditor') %>

