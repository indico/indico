<table width="100%" class="ACtab"><tr><td>
<br>
<table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle"> <%= _("Access control")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Current status")%></span></td>
		<form action="<%= setPrivacyURL %>" method="POST">
        <td bgcolor="white" width="100%" valign="top" class="blacktext">
            <%= locator %>
    <b><%= privacy %></b><br/>
    <small>
    <%= changePrivacy %>
    </small>
        </td>
		</form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Users allowed to access")%></span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext"><%= userTable %></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Visibility to unauthorized users")%></span></td>
		<form action="<%= setVisibilityURL %>" method="POST">
        <td bgcolor="white" width="100%" valign="top" class="blacktext">
            <%= locator %>
            <b><%= visibility %></b>
			<small><%= changeVisibility %></small>
        </td>
		</form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Access key")%></span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">
		<form action="<%= setAccessKeyURL %>" method="POST">
            	<%= locator %>
		<input name="accessKey" type="password" size=25 value="<%= accessKey %>">
		<input type="submit" class="btn" value="<%= _("change")%>">
		</form>
	</td>
    </tr>
</table>
<%= domainControlFrame %>
<br>
</tr></td></table>