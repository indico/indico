
<form action="${ postURL }" method="POST">
    <table width="100%" align="center">
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td>
                <table style="border:1px solid #777777;" align="center">
                    <tr><td>&nbsp;</td></tr>
                    <tr>
                        <td align="center"> ${ _("You are going to recover to the conference the abstract titled")}: </td>
                    </tr>
                    <tr>
                        <td align="center"> "<b>${ title }<b>".</td>
                    </tr>
                    <tr><td>&nbsp;</td></tr>
                </table>
            </td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td align="center">
                <input type="submit" class="btn" name="OK" value="${ _("confirm")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
