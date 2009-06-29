<form action="%(postURL)s" method="POST">
    %(locator)s
    <input type="hidden" name="typeMaterial" value="paper">
    <table>
        <tr>
            <td colspan="2" align="center">%(Wtitle)s</td>
        </tr>
        <tr>
            <td align="right"> <%= _("Title")%></td>
            <td align="left"><input type="text" name="title" value="%(title)s"></td>
        </tr>
        <tr>
            <td align="right"> <%= _("Abstract")%></td>
            <td align="left"><textarea name="description" cols="43" rows="6">%(description)s</textarea></td>
        </tr>
        <tr>
            <td colspan="2" align="center"><input type="submit" class="btn" value="<%= _("ok")%>"></td>
        </tr>
    </table>
</form>
