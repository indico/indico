<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Modifying further information (basic data)")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td align="left"><input type="text" name="title" size="60" value="${ title }"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Content")}</span></td>
            <td align="left"><textarea name="content" cols="100" rows="10">${ content }</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" class="btn" value="${ _("OK")}">&nbsp;<input type="submit" class="btn" value="${ _("cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
