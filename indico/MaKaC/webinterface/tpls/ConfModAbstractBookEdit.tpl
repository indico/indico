<form action=<%= postURL %> method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Customisation of abstracts book")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Additional text")%></span></td>
            <td bgcolor="white" width="100%">
                <textarea name="text" cols="80" rows="10"><%= text %></textarea>
            </td>
        </tr>
		<tr><td>&nbsp;</td></tr>
        <tr align="left">
            <td align="left" width="100%" colspan="2">
                <table align="left" width="100%">
                    <tr>
                        <td align="left">
							<input type="submit" class="btn" value="<%= _("ok")%>" name="EDIT">
							<input type="submit" class="btn" value="<%= _("cancel")%>" name="CANCEL">
						</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>

