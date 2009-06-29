<table boder="0">
    <tr>
        <form action="%(removeUsersURL)s" method="POST">%(locator)s
        <td colspan="2">%(userItems)s</td>
    </tr>
    <tr>
        <td><input type="submit" class="btn" value="<%= _("remove")%>"></form></td>
        <td><form action="%(addUsersURL)s" method="POST">
                <input type="submit" class="btn" value="<%= _("add")%>">
            </form>
        </td>
    </tr>
</table>
