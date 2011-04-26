
<table width="42%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2">${ _("Rejecting an abstract")}</td>
    </tr>
    <tr>
        <td>&nbsp;&nbsp;&nbsp;</td>
        <td bgcolor="white" align="left">
            <br>
            <form action=${ rejectURL } method="POST">
                <input type="hidden" name="comments" value=${ comments }>
                <input type="hidden" name="confirm" value="True">
                <font size="+1" color="red">${ _("WARNING")}!!</font> ${ _("No notification template has been found.")}<br>
                ${ _("If you still want to proceed with the rejection, please press \"Reject\" but please note that the abstract authors will not be notified by mail.")}
                <br><br>
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <table align="left">
                <tr>
                    <td align="left">
                            <input type="submit" class="btn" name="reject" value="${ _("Reject")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
