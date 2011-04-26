<form action=${ postURL } method="post">
    <input type="hidden" name="reportNumberSystem" value="${ reportNumberSystem }">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Report number - system")} <b>"${ system }"</b></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Report number")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="reportNumber" value="${ reportNumber }" size="40"></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td align="left" colspan="2"><input type="submit" class="btn" value="${ _("save")}" name="save"> <input type="submit" class="btn" value="${ _("Cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
