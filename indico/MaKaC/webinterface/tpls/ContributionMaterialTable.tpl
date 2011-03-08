<table border="0">
    <tr>
        <form action="${ deleteURL }" method="POST">${ locator }
        <td colspan="2">
            <table>${ items }</table>
        </td>
    </tr>
    <tr>
        <td><input type="submit" class="btn" value="${ _("remove")}"></form></td>
        <td><form action="${ addURL }" method="POST"><select name="typeMaterial"><option value="misc" selected>${ _("Additional material")}</option>${ matTypesSelectItems }</select><input type="submit" class="btn" value="${ _("add")}"></form></td>
    </tr>
</table>