<form method="POST" action=${ postURL }>
    <table width="100%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="2" class="groupTitle"> ${ _("Importing contributions to a session")}</td>
        </tr>
        <tr><td colspan="2">&nbsp;</td></tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Contribution with ids")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="selContribs" size="30" value=""></td>
        </tr>
        <tr><td colspan="2">&nbsp;</td></tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("All contributions from track")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <select name="selTrack">${ tracks }</select>
            </td>
        </tr>
        <tr><td colspan="2">&nbsp;</td></tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Selected contributions from the following list")}</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <table width="100%">
                    ${ availContribs }
                </table>
        </tr>
        <tr><td colspan="2">&nbsp;</td></tr>
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
