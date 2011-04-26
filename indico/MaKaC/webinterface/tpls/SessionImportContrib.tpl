<table align="center" bgcolor="#EAEAEA" width="100%">
    <tr>
        <td align="left"></td>
        <td align="left"> ${ _("id")}</td>
        <td align="left" width="100%"> ${ _("title")}</td>
        <td align="left"> ${ _("type")}</td>
        <td align="left"> ${ _("presenter")}</td>
        <td align="left"> ${ _("session")}</td>
        <td align="left"> ${ _("track")}</td>

    </tr>
    <form action=${ postURL } method="post">
        ${ contributions }
    <tr>
        <td colspan="7">
            <table><tr>
                <td><input type="submit" class="btn" name="addContrib" value="${ _("import")}"></td><td> <input type="submit" class="btn" name="cancel" value="${ _("cancel")}"></td>
            </tr></table>
        </td>
    </tr>
    </form>
</table>
