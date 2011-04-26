
<table width="98%" cellspacing="1" align="center">
    <tr>
        <form action=${ newCommentURL } method="POST">
        <td style="border-top:2px solid #777777; background:#F6F6F6">
            <input type="submit" class="btn" value="${ _("new comment")}">
        </td>
        </form>
    </tr>
    ${ comments }
    <tr>
        <form action=${ newCommentURL } method="POST">
        <td style="border-bottom:2px solid #777777; background:#F6F6F6">
            <input type="submit" class="btn" value="${ _("new comment")}">
        </td>
        </form>
    </tr>
</table>
