
<form action="<%= removeIdentityURL %>" method="POST" style="margin: 0;">
<table>
    <%= items %>
    <tr>
        <td>
        <table>
            <tr>
                <td>
                    <input type="submit" class="btn" value="<%= _("delete selected accounts")%>" name="action">
                    </form>
                </td>

                <td>
                <form style="margin: 0; padding: 0;" action="<%= addIdentityURL %>" method="POST">
                    <input type="submit" class="btn" value="<%= _("create a new account")%>" name="action">
                </form>

                </td>
            </tr>
        </table>
        </td>
    </tr>
</table>