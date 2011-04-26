<form action="${ postURL }" method="POST">
    ${ locator }
    <input type="hidden" name="typeMaterial" value="paper">
    <table>
        <tr>
            <td colspan="2" align="center">${ Wtitle }</td>
        </tr>
        <tr>
            <td align="right"> ${ _("Title")}</td>
            <td align="left"><input type="text" name="title" value="${ title }"></td>
        </tr>
        <tr>
            <td align="right"> ${ _("Abstract")}</td>
            <td align="left"><textarea name="description" cols="43" rows="6">${ description }</textarea></td>
        </tr>
        <tr>
            <td colspan="2" align="center"><input type="submit" class="btn" value="${ _("ok")}"></td>
        </tr>
    </table>
</form>
