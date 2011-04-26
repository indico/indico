
<table align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td nowrap class="groupTitle"> ${ _("Unmerging an abstract")}</td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td>
            <table>
                <tr>
                    <form action=${ unmergeURL } method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="OK" value="${ _("confirm")}">
                    </td>
                    </form>
                    <td>
                    <form action=${ cancelURL } method="POST">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
