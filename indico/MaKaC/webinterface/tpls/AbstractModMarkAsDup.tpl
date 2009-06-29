
<table width="50%%" align="center" border="0" style="border-left: 1px solid #777777">
	<tr>
		<td class="groupTitle" colspan="2"> <%= _("Marking an abstract as a duplicate")%></td>
    </tr>
    <tr>
        <td bgcolor="white">
            <br>
            <table width="100%%">
                %(error)s
                <tr>
					<form action=%(duplicateURL)s method="POST">
					<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Comments")%></span></td>
					<td>&nbsp;
						<textarea name="comments" rows="6" cols="50">%(comments)s</textarea>
					</td>
                </tr>
                <tr>
                    <td colspan="2"><br></td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Original abstract id")%></span></td>
                    <td>&nbsp;
                        <input type="text" name="id" value=%(id)s>
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td align="left">
            <table align="left">
                <tr>
                    <td align="left">
						<input type="submit" class="btn" name="OK" value="<%= _("confirm")%>">
					</td>
					</form>
					<form action=%(cancelURL)s method="POST">
                    <td align="left">
						<input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
					</td>
					</form>
                </tr>
            </table>
        </td>
    </tr>
</table>
