
<table width="100%%" align="center" border="0">
    <tr>
        <td colspan="5" class="groupTitle"> <%= _("Access control")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Current status")%></span></td>
		<form action="%(setPrivacyURL)s" method="POST">
        <td bgcolor="white" width="100%%" valign="top" class="blacktext">
            %(locator)s
    <b>%(privacy)s</b><br/>
    <small>
    %(changePrivacy)s
    </small>
        </td>
		</form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Users allowed to access")%></span></td>
        <td bgcolor="white" width="100%%" valign="top" class="blueLineBottom">%(userTable)s</td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat"><%= _("Access key")%></span></td>
        <td bgcolor="white" width="100%%" valign="top" class="blacktext">
		<form action="%(setAccessKeyURL)s" method="POST">
            	%(locator)s
		<input name="accessKey" type="password" size=25 value="%(accessKey)s">
		<input type="submit" class="btn" value="<%= _("change")%>">
		</form>
	</td>
    </tr>
</table>
