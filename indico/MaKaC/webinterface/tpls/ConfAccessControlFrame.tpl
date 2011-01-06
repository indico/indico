
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
    		<form action="%(setAccessKeyURL)s" method="POST" onsubmit="if(this.accessKey.value) return confirm('<%=_("Please note that it is more secure to make the event private instead of using an access keyy.")%>');">
                	%(locator)s
    		<input name="accessKey" type="password" size=25 value="%(accessKey)s">
    		<input type="submit" class="btn" value="<%= _("change")%>">
    		<div class="warningText"><%=_("Note: It is more secure to use make the event private instead of using an access key!")%></div>
    		</form>
	    </td>
    </tr>
</table>
