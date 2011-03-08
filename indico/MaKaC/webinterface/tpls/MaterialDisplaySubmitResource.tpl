<br>
<form action=${ postURL } method="POST" enctype="multipart/form-data">
<table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle"> ${ _("Submitting resource")}</td>
    </tr>
    ${ errors }
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"> ${ _("Contribution")}</span>
        </td>
        <td bgcolor="white" width="80%">${ contribId }-${ contribTitle }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"> ${ _("Material type")}</span>
        </td>
        <td bgcolor="white" width="80%">${ matType }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"> ${ _("File to submit")}</span>
        </td>
        <td bgcolor="white" width="80%">
            <input type="file" name="file">
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"> ${ _("Description & comments")}</span>
        </td>
        <td bgcolor="white" width="80%">
            <textarea name="description" cols="43" rows="6">${ description }</textarea>
        </td>
    </tr>
    <tr>
        <td colspan="2">&nbsp;</td>
    </td>
    <tr>
        <td>
            <input type="submit" class="btn" name="OK" value="${ _("submit")}">
            <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}">
        </td>
    </tr>
</table>
</form>
<br>