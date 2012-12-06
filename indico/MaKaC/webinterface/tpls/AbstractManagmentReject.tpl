
<table width="60%" align="left" border="0" style="padding: 10px 0 0 10px;">
    <tr>
        <td class="groupTitle" colspan="2"> ${ _("Rejecting abstract")}</td>
    </tr>
    % if trackTitle:
    <tr>
        <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Abstract title")}</span></td>
        <td style="font-weight:bold;">${ abstractName }</td>
    </tr>
    % endif
    <tr>
        <form action=${ rejectURL } method="POST">
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Comments")}</span></td>
        <td colspan="2"><textarea name="comments" rows="6" cols="50"></textarea></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
    % if showNotifyCheckbox:
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email Notification")}</span></td>
        <td>
            <input type="checkbox" name="notify" value="true" checked> ${ _("Send the automatic notification of acceptance using the Email Template created by the manager")}
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    % endif
    <tr>
        <td align="center" colspan="2">
            <table align="center">
                <tr>
                    <td align="left">
                        <input type="submit" class="btn" name="reject" value="${ _("reject")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
