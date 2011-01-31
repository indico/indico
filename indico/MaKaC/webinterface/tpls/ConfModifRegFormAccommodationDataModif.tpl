<form action=<%= postURL %> method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Modifying accommodation (basic data)")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
            <td align="left"><input type="text" name="title" size="60" value="<%= title %>"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Arrival dates (offset)")%></span></td>
            <td align="left">
            <%= _("event start date offset:")%> <input type="text" name="aoffset1" size="2" value="<%= aoffset1 %>"> <%= _("""days ->
            event end date offset:""")%> <input type="text" name="aoffset2" size="2" value="<%= aoffset2 %>"> days
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Departure dates (offset)")%></span></td>
            <td align="left">
            <%= _("event start date offset:")%> <input type="text" name="doffset1" size="2" value="<%= doffset1 %>"> <%= _("""days ->
            event end date offset:""")%> <input type="text" name="doffset2" size="2" value="<%= doffset2 %>"> days
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
            <td align="left"><textarea name="description" cols="100" rows="10"><%= description %></textarea></td>
        </tr>
		<tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" class="btn" value="<%= _("OK")%>">&nbsp;<input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel"></td>
        </tr>
    </table>
</form>