<table border="0" width="100%%">
    <tr>
        <form action="%(deleteURL)s" method="POST">%(locator)s
        <td width="70%%" colspan="2">
            <table>%(items)s</table>
        </td>
		<td width="30%%" valign="bottom" align="right">
				<input type="submit" class="btn" value="<%= _("remove")%>">
			</form>
			<form action="%(addURL)s" method="POST">
				<select name="typeMaterial">
                    <option value="notype" selected>--  <%= _("select a type")%> --</option>
					<option value="misc"> <%= _("Additional material")%></option>
					%(matTypesSelectItems)s
				</select><input type="submit" class="btn" value="<%= _("add")%>">
		</td>
		</form>
    </tr>
</table>
