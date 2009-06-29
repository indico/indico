<table width="100%%">
    <tr>
        <td>&nbsp;</td>
    </tr>
    <tr>
        <td>
            <form action=%(displayURL)s method="POST">
			<table width="100%%" align="center" border="0" 
                    style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
				<tr>
					<td class="groupTitle" 
                            style="background:#E5E5E5; color:gray">
                        &nbsp;&nbsp;&nbsp;<%= _("Display options")%>
                    </td>
				</tr>
				<tr>
					<td>
                        <span class="titleCellFormat"><%= _("View mode")%> </span>
                            <select name="view">%(viewModes)s</select>
                          
                    </td>
                </tr>
				<tr>
					<td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="<%= _("apply")%>"></td>
				</tr>
            </table>
            </form>
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
	<tr>
		<td>
			<table width="100%%" align="center" border="0" 
                    style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
                <tr>
					<td colspan="9" class="groupTitle" style="background:#E5E5E5; color:gray">
                        &nbsp;&nbsp;&nbsp;<%= _("Speakers")%>
                    </td>
				</tr>
                <tr>
                    <td align="center" colspan="2">
                        %(letterIndex)s
                    </td>
                </tr>
                <tr>
                    <td align="center" colspan="2">&nbsp;</td>
                </tr>
           %(items)s
            </table>
        </td>
	</tr>
</table>
