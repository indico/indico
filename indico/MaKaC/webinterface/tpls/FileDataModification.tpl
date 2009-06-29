<table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Modifying file data")%></td>
    </tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
        <td align="left"><input type="text" name="title" size="60" value="%(title)s"></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
        <td align="left"><textarea name="description" cols="43" rows="6">%(description)s</textarea></td>
    </tr>
	<tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2" align="left"><input type="submit" class="btn" value="<%= _("ok")%>"></td>
    </tr>
</table>
