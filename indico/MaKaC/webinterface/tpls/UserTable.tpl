<table boder="0">
    <tr>
        <form action="${ removeUsersURL }" method="POST">${ locator }
        <td colspan="2">${ userItems }</td>
    </tr>
    <tr>
        <td><input type="submit" class="btn" value="${ _("remove")}"></form></td>
        <td><form action="${ addUsersURL }" method="POST">
                <input type="submit" class="btn" value="${ _("add")}">
            </form>
        </td>
    </tr>
</table>
