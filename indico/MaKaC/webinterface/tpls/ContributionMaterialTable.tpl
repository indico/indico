<table border="0">
    <tr>
        <form action="%(deleteURL)s" method="POST">%(locator)s
        <td colspan="2">
            <table>%(items)s</table>
        </td>
    </tr>
    <tr>
        <td><input type="submit" class="btn" value="<%= _("remove")%>"></form></td>
        <td><form action="%(addURL)s" method="POST"><select name="typeMaterial"><option value="misc" selected><%= _("Additional material")%></option>%(matTypesSelectItems)s</select><input type="submit" class="btn" value="<%= _("add")%>"></form></td>
    </tr>
</table>
