
<table width="100%%" align="center">
    <tr>
        <td><br>
        </td>
    </tr>
    <tr>
        <td>
            <table style="border-left:1px solid #777777;border-top:1px solid #777777;" width="95%%" align="center" cellspacing="0">
				<tr>
					<td class="groupTitle" colspan="4" style="background:#E5E5E5; color:gray; border-top:2px solid #FFFFFF; border-left:2px solid #FFFFFF">&nbsp;&nbsp;&nbsp; <%= _("Abstracts")%></td>
				</tr>
				<tr>
					<td colspan="4">&nbsp <%= _("Click on the title of an abstract to see its details, or if you want to modify or withdraw it")%></td>
				</tr>
                <tr>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("ID")%></td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Title")%></td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Status")%></td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Modification date")%></td>
                </tr>
                <form action=%(abstractsPDFURL)s method="post" target="_blank">
                %(abstracts)s
				<tr><td colspan="4">&nbsp;</td></tr>
				<tr>
                    <td align="center" colspan="4">
                        <input type="submit" class="btn" value="<%= _("get PDF of selected abstracts")%>">
                    </td>
					</form>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>

