<table width="100%" class="ACtab"><tr><td>
<br>
${ modifyControlFrame }
<br>
${ accessControlFrame }
<br>
<table class="groupTable">
    <tr>
        <td colspan="3"><div class="groupTitle">${ _("Submission control")}</div></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Submitters")}<br><font size="-2">(${ _("users allowed to submit material for this contribution")})</font></span></td>
        <form action=${ remSubmittersURL } method="POST">
        <td bgcolor="white" width="80%" valign="top" class="blacktext">${ submitters }</td>
        <td align="right">
            <input type="submit" class="btn" value="${ _("remove")}">
        </form>
        <form action=${ addSubmittersURL } method="POST">
            <input type="submit" class="btn" value="${ _("add")}">
        </form>
        </td>
    </tr>
</table>
<br>
</tr></td></table>
