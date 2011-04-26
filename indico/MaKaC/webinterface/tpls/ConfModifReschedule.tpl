<form method="POST" action=${ postURL }>
    <input type="hidden" name="targetDay" value=${ targetDay }>
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle">${ _("Reschedule entries")}</td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Time between entries<br>(hh:mm)")}</span></td>
            <td bgcolor="white" width="100%" valign="top">&nbsp;
                <input type="text" size="2" name="hour" value="00">:<input type="text" size="2" name="minute" value="00">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Action")}:</span></td>
            <td style="padding-left:10px">
                <input type="radio" name="action" value="startingTime" checked>${ _("compute entries starting time")}<br>
                <input type="radio" name="action" value="duration">${ _("compute entries duration")}
            </td>
        </tr>

        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
        <input type="submit" class="btn" value="ok" name="${ _("OK")}">
        <input type="submit" class="btn" value="cancel" name="${ _("CANCEL")}">
            </td>
        </tr>
    </table>
</form>
