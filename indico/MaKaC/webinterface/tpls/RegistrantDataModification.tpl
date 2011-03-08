<form action=${ postURL } method="POST">
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Modifying registrant data")}</td>
        </tr>
        ${ data }
        <tr><td>&nbsp;</td></tr>
        <tr align="left">
            <td align="left" width="100%" colspan="2">
                <table align="left" width="100%">
                    <tr>
                        <td align="left">
                            <input type="submit" class="btn" value="${ _("ok")}">
                            <input type="submit" class="btn" value="${ _("cancel")}" name="cancel">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
