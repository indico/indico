<form action="${ postURL }" method="POST">
    <table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"> ${ _("Select the main resource")}</td>
        </tr>
        <tr>
            <td>
                <br>${ resources }
            <td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left">
                <input type="submit" class="btn" value="${ _("ok")}" value="ok">
                <input type="submit" class="btn" value="${ _("cancel")}" name="cancel">
            </td>
        </tr>
    </table>
</form>
