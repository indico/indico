
<table width="100%">
    <tr>
        <td>
            <form action=${ displayURL } method="POST">
            <table width="100%" align="center" border="0">
                <tr>
                    <td class="groupTitle">${ _("Display options")}</td>
                </tr>
                <tr>
                    <td>
                        <div class="titleCellFormat" style="padding: 10px;">
                            ${ _("View mode")} <select name="view">${ viewModes }</select> &nbsp;&nbsp;&nbsp;
                            <input type="submit" class="btn" name="OK" value="${ _("apply")}">
                        </div>
                    </td>
                </tr>
            </table>
            </form>
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
    <tr>
        <td>
            <table width="100%" align="center" border="0">
                <tr>
                    <td colspan="9" class="groupTitle" style="">${ _("Authors")}</td>
                </tr>
                <tr>
                    <td align="center" colspan="2">
                        ${ letterIndex }
                    </td>
                </tr>
                <tr>
                    <td align="center" colspan="2">&nbsp;</td>
                </tr>
           ${ items }
            </table>
        </td>
    </tr>
</table>
