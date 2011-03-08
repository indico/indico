
<table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2"> ${ _("Merging an abstract into another")}</td>
    </tr>
    <tr>
        <td bgcolor="white">
            <br>
            <table width="100%">
                ${ error }
                <tr>
                    <form action=${ mergeURL } method="POST">
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Comments")}</span></td>
                    <td>&nbsp;
                        <textarea name="comments" rows="6" cols="50">${ comments }</textarea>
                    </td>
                </tr>
                <tr>
                    <td colspan="2"><br></td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Target abstract id")}</span></td>
                    <td>&nbsp;
                        <input type="text" name="id" value=${ id }>
                    </td>
                </tr>
                <tr>
                    <td>&nbsp;</td>
                    <td align="left">
                        <input type="checkbox" name="includeAuthors"${ includeAuthorsChecked }><font color="gray"> ${ _("Include authors into the target abstarct")}</font>
                    </td>
                </tr>
                <tr>
                    <td align="center" colspan="2">
                        <input type="checkbox" name="notify"${ notifyChecked }><font color="gray">${ _("Automatic email notification")}</font>
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td>
            <table align="left">
                <tr>
                    <td align="left" valign="top">
                        <input type="submit" class="btn" name="OK" value="${ _("confirm")}">
                    </td>
                    </form>
                    <td align="left" valign="top">
                        <form action=${ cancelURL } method="POST">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>