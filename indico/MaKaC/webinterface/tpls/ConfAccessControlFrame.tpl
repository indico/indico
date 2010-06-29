
<table width="100%%" align="center" border="0">
    <tr>
        <td colspan="5" class="groupTitle"> <%= _("Access control")%></td>
    </tr>
    <tr>
        <td colspan="5" style="height: 10px"></td>
    </tr>
<% includeTpl('AccessControlStatusFrame', parentName=parentName, privacy=privacy, \
    parentPrivacy=parentPrivacy, statusColor = statusColor, parentStatusColor=parentStatusColor,\
    locator=locator, isFullyPublic=isFullyPublic) %>
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
