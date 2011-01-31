<form action=<%= postURL %> method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Modifying Sessions (basic data)")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
            <td align="left"><input type="text" name="title" size="60" value="<%= title %>"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
            <td align="left"><textarea name="description" cols="100" rows="10"><%= description %></textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Type of sessions' form")%><br><small>( <%= _("how many sessions the<br>registrant can choose<br>please note that billing <br>not possible when using '2 choices'")%> )</small></span></td>
            <td align="left"><%= types %></td>
        </tr>
		<tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" class="btn" value="<%= _("OK")%>">&nbsp;<input type="submit" class="btn" value="cancel" name=" <%= _("cancel")%>"></td>
        </tr>
    </table>
</form>