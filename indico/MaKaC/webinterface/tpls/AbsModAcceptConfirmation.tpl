
<table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2"> ${ _("Accepting abstract")}</td>
    </tr>
    <tr>
        <td>&nbsp;&nbsp;&nbsp;</td>
        <td bgcolor="white" align="left">
            <br>
            <form action=${ acceptURL } method="POST">
                <input type="hidden" name="track" value=${ track }>
                <input type="hidden" name="session" value=${ session }>
                <input type="hidden" name="comments" value=${ comments }>
                <input type="hidden" name="type" value=${ type }>
                <input type="hidden" name="confirm" value="True">
                <font size="+1" color="red">${ _("WARNING")}!!</font> ${ _("No notification template has been found.")}<br>
                ${ _("""If you still want to proceed with the acceptance, please press "Accept" but please note that the abstract authors will not be notified by email.""")}
                <br><br>
        </td>
    </tr>
    <tr>
        <td colspan="2" align="left">
            <table align="left">
                <tr>
                    <td align="left">
                            <input type="submit" class="btn" name="accept" value="${ _("Accept")}">
            </form>
                    </td>
                    <td align="left">
                        <form action=${ cancelURL } method="POST">
                            <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
