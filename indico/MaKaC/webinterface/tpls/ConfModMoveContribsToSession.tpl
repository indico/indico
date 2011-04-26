<form method="POST" action=${ postURL }>
    <table width="60%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle">${ _("Moving contributions into a session")}</td>
        </tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat">${ _("Contribution ids to be moved")}</span></td>
            <td bgcolor="white">&nbsp;
            <input type="text" name="contributions" size="60" value=${ contribs }></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Target session")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <select name="targetSession">${ sessions }</select>
            </td>
        </tr>
 <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
                <table align="center">
                    <tr>
                        <td><input type="submit" class="btn" value="${ _("submit")}" name="OK"></td>
                        <td><input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
