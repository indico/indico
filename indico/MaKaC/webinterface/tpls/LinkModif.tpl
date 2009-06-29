<br>
<table width="90%%" align="center" valign="middle" style="padding-top:20px" border="0">
	<tr>
		<td colspan="3" class="subgroupTitle"> <%= _("External link")%></td>
	</tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Name")%></span></td>
        <td bgcolor="white" width="100%%"><font size="+1"><b>&nbsp;&nbsp;&nbsp;%(linkName)s</b></font></td>
        <td rowspan="2" valign="top" align="right"><form action=%(dataModificationURL)s method="POST"><input type="submit" class="btn" value="<%= _("modify")%>" ></form></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("URL")%></span></td>
        <td bgcolor="white" width="100%%"><b>&nbsp;&nbsp;&nbsp;%(linkURL)s</b></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Display target")%></span></td>
        <td bgcolor="white" width="100%%" ><b>&nbsp;&nbsp;&nbsp;%(displayTarget)s</b>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Status")%></span></td>
        <form action=%(toggleLinkStatusURL)s method="post">
            <td bgcolor="white" width="100%%" colspan="2"><b>&nbsp;&nbsp;&nbsp;%(linkStatus)s</b> <input type="submit" class="btn" value="%(changeStatusTo)s" ></td>
        </form>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Position")%></span></td>
        <td bgcolor="white" width="100%%" colspan="2">
        <table><tr><td>
            <a href=%(moveUpURL)s>&nbsp;&nbsp;&nbsp;<img class="imglink" src=%(imageUpURL)s alt="<%= _("move up")%>"></a> <%= _("move the link up")%>
            </td></tr>
            <tr><td>
            <a href=%(moveDownURL)s>&nbsp;&nbsp;&nbsp;<img class="imglink" src=%(imageDownURL)s alt="<%= _("move down")%>"></a> <%= _("move the link down")%>
            </td></tr></table
        </td>
    </tr>
    <tr>
        <td bgcolor="white" width="100%%" colspan="3">
			<br>
            <table width="100%%" align="center" bgcolor="white" border="0" style="border-top:1px solid #777777">
                <tr>
                    <form action=%(addSubLinkURL)s method="POST">
                        <td bgcolor="white" align="right" width="50%%">
                            <input type="submit" class="btn" value="<%= _("add sub link")%>" >
                        </td>
                    </form>
                    <form action=%(removeLinkURL)s method="POST">
                        <td bgcolor="white" align="left" width="50%%">
                            <input type="submit" class="btn" value="<%= _("remove this link")%>" >
                        </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
