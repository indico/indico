<div class="groupTitle"> <%= _("Creating new track (basic data)")%></div>

<form method="POST" action="%(postURL)s">
    %(locator)s
    <table width="100%%" border="0">
        <tr>
			<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
            <td bgcolor="white" width="100%%"><input type="text" name="title" size="60" value="%(title)s"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
            <td bgcolor="white" width="100%%"><textarea name="description" cols="43" rows="6">%(description)s</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="left">
        <td>&nbsp;</td>
            <td>
                <table align="left">
                    <tr>
                        <td><input type="submit" class="btn" value="<%= _("ok")%>"></td>
                        <td><input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
