<table align="center" width="100%">
    <tr>
        <td align="center">
        <font size="+2">${msg}<br> ${ _("This event is protected with a modification key.")}</font>
    </td>
    </tr>
    <tr>
        <td align="center">
        <form action=${url} method="POST">
        %if not _session.user:
            <a class="loginHighlighted" style="padding:4px 17px" href="${ url_for_login(_request.relative_url) }"><strong style="color: white;">Login</strong></a>&nbsp;${ _("or enter the modification key here:")}
        %else:
            ${ _("Please enter it here:")}
        % endif
        <input type="hidden" name="redirectURL" value=${redirectURL}>
        <input name="modifKey" type="password">
        <input type="submit" class="btn" value="${ _("go")}">
        </form>
        </td>
    </tr>
</table>
