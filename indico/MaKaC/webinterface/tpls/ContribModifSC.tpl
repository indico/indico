<br>
<table width="90%" align="center" border="0"
                                    style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="4">${ _("Sub Contribution")}</td>
    </tr>
    <tr>
        <td bgcolor="white" width="100%" colspan="4">
            <form action="${ deleteItemsURL }" method="POST">
              <table bgcolor="white" border="0" cellspacing="0">
                ${ subContList }


        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="3" class="buttonsSeparator" valign="bottom" align="left">
            <table align="center">
                <tr>
                    <td valign="bottom" align="center">
                            <input type="submit" class="btn" value="${ _("remove selected")}">
                    </td>
                    </form>
                    <form action="${ addSubContURL }" method="POST">
                    <td>
                        <input type="submit" class="btn" value="${ _("add sub contribution")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
