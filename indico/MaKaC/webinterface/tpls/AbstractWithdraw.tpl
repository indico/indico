
<form action="${ postURL }" method="POST">
    <table width="100%" align="center">
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td style="padding:25px"> ${ _("You are going to withdraw from this conference the abstract titled")} "<b>${ title }<b>".</td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td style="padding-left:25px; padding-right:25px"> ${ _("Please enter below a comment to justify the withdrawal of this abstract")}:</font><br></td>
        </tr>
        <tr>
            <td align="left" style="padding-left:50px; padding-right:25px">
                <textarea name="comment" rows="8" cols="60"></textarea>
            </td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td align="center" style="border-top:1px solid #777777; padding:25px; padding-top:10px">
                <input type="submit" class="btn" name="OK" value="${ _("withdraw")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
