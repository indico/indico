<form action=${ saveURL } method="post">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Contribution Type")} : <i>${ ctName }</i></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
            <td bgcolor="white" width="100%"><input type="text" name="ctName" value="${ ctName }" size="40"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td bgcolor="white" width="100%"><textarea name="ctDescription" rows="8" cols="70">${ ctDescription }</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td align="left" colspan="2"><input type="submit" class="btn" value="${ _("save")}" name="save"> <input type="submit" class="btn" value="${ _("Cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
