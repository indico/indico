<form action=${ postURL } method="POST">
    <table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"> ${ _("Editing Session comment")}</font></b>
            </td>
        </tr>
        <tr>
            <td>
                <textarea name="content" rows="10" cols="85">${ comment }</textarea>
            </td>
        </tr>
        <tr>
            <td align="left">
                <input type="submit" class="btn" name="OK" value="${ _("submit")}">
                <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
