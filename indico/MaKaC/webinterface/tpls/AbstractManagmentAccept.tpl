
<table width="50%%" align="center" border="0" style="border-left: 1px solid #777777">
	<tr>
		<td class="groupTitle"><%= _("Accepting abstract")%></td>
    </tr>
    <tr>
        <td bgcolor="white">
            <table>
                <tr>
					<form action=%(acceptURL)s method="POST">
					<td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Comments")%></span></td>
					<td><textarea name="comments" rows="6" cols="50"></textarea></td>
				</tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Destination track")%></span></td>
                    <td>
                        <select name="track">
                            %(tracks)s
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Destination session")%></span></td>
                    <td>
                        <select name="session">
                            %(sessions)s
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Type of contribution")%></span></td>
                    <td>
                        <select name="type">
                            %(types)s
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Email Notification")%></span></td>
                    <td>
                        <input type="checkbox" name="notify" value="true" checked><%= _(" Automatic Email Notification")%>
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td valign="bottom" align="left">
            <table valign="bottom" align="left">
                <tr>
                    <td valign="bottom" align="left">
						<input type="submit" class="btn" name="accept" value="<%= _("accept")%>">
                    </td>
					</form>
					<form action=%(cancelURL)s method="POST">
                    <td valign="bottom" align="left">
						<input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
                    </td>
					</form>
                </tr>
            </table>
        </td>
    </tr>
</table>
