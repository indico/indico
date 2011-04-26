<table border="0" width="100%">
    <tr>
        <form action="${ deleteURL }" method="POST">${ locator }
        <td width="70%" colspan="2">
            <table>${ items }</table>
        </td>
        <td width="30%" valign="bottom" align="right">
                <input type="submit" class="btn" value="${ _("remove")}">
            </form>
            <form action="${ addURL }" method="POST">
                <select name="typeMaterial">
                    <option value="notype" selected>--  ${ _("select a type")} --</option>
                    <option value="misc"> ${ _("Additional material")}</option>
                    ${ matTypesSelectItems }
                </select><input type="submit" class="btn" value="${ _("add")}">
        </td>
        </form>
    </tr>
</table>
