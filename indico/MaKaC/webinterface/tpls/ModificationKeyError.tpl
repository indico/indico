<table align="center" width="100%">
    <tr>
        <td align="center">
        <font size="+2">${msg}<br> ${ _("This event is protected with a modification key.")}</font>
    </td>
    </tr>
    <tr>
        <td align="center">
        <form action=${url} method="POST">
        ${ _("Please enter it here:")}
        <input type="hidden" name="redirectURL" value=${redirectURL}>
        <input name="modifKey" type="password">
        <input type="submit" class="btn" value="${ _("go")}">
        </form>
        </td>
    </tr>
</table>
