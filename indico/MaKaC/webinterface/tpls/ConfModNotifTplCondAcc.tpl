<form action=${ postURL } method="POST">
    <input type="hidden" name="condType" value=${ condType }>
    <table width="50%" cellspacing="0" align="left" border="0" style="padding-left:5px; padding-top:5px;">
		<tr>
			<td colspan="2" class="groupTitle">${ _("New condition for status")} <b>${ _("ACCEPTED")}</b></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD" style="padding-top:10px; padding-left:10px;">
                <span class="titleCellFormat">${ _("Contribution type")}</span>
            </td>
			<td style="padding-top:10px;">
				<select name="contribType">${ contribTypeItems }</select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD" style="padding-top:5px; padding-left:10px;"><span class="titleCellFormat">${ _("Track")}</span></td>
			<td style="padding-top:5px;">
                <select name="track">${ trackItems }</select>
            </td>
        </tr>
		<tr align="center">
			<td colspan="3" valign="bottom" align="center" style="padding-top:15px;">
                <input type="submit" class="btn" name="OK" value="${ _("submit")}">
                <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
