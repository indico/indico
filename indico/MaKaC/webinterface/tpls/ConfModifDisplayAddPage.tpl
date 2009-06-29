
<table width="100%%">
    <tr>
        <form action=%(saveLinkURL)s method="POST">
        <td bgcolor="white" width="90%%" valign="top" style="padding-left:20px">
                <table width="60%%" align="left" valign="middle" style="padding-top:20px" border="0">
					<tr>
						<td colspan="2" class="subgroupTitle"> <%= _("Create internal page web")%></td>
					</tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Name")%></span></td>
                        <td bgcolor="white" width="100%%"><input type="text" name="name" size="50"></td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Content")%></span></td>
                        <td style="border:1px solid #000000"><textarea  id="content" name="content" cols="80" rows="40">%(content)s</textarea></td>
                    </tr>
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Display target")%></span></td>
                        <td bgcolor="white" width="100%%">
                          <input type="radio" name="displayTarget" value="" CHECKED> <%= _("Display in the SAME window")%><br>
                          <input type="radio" name="displayTarget" value="_blank"> <%= _("Display in a NEW window")%>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="white" colspan="2" align="center" width="100%%">
                            <input type="submit" class="btn" name="submit" value="<%= _("save")%>">
                            <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>
<br>

