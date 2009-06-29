<form action=%(postURL)s method="POST">
    <input type="hidden" name="condType" value=%(condType)s>
    <table width="50%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
		<tr>
			<td colspan="2" class="groupTitle"><%= _("New condition for status")%> <b><%= _("ACCEPTED")%></b></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Contribution type")%></span></td>
			<td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
				<select name="contribType">%(contribTypeItems)s</select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Track")%></span></td>
			<td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <select name="track">%(trackItems)s</select>
            </td>
        </tr>
        <tr><td colspan="3">&nbsp;</td></tr>
		<tr align="center">
			<td colspan="3" style="border-top:1px solid #777777;" valign="bottom" align="center">
                <input type="submit" class="btn" name="OK" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
