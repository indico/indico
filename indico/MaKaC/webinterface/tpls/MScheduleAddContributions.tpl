WMScheduleAddContributions template
<form method="POST" action=${ postURL }>
    ${ targetDay }
    <table width="100%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Adding contributions")}</td>
        </tr>
        <tr>
            <td></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Contribution ids to be added")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="selContribs" size="30" value=""></td>
        </tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Selected contributions from the following list")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <table>
                    ${ contribs }
                </table>
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
