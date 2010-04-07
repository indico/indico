<script type="text/javascript">

function showAbstracts()
{
    var listOfAbstracts = <%= listOfAbstracts %>;
    var div = Html.div({});
    for (a in listOfAbstracts)
    {
        div.append(listOfAbstracts[a]);
        div.append(Html.br());
    }
    var popup = new AlertPopup(Html.span('warningTitle', "List of abstracts"), div);
    popup.open();
}


</script>


<table width="50%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2"> <%= _("Rejecting abstract")%><a href="javascript:showAbstracts()">(%(abstractsQuantity)s)</a></td>
    </tr>
    <tr>
        <form action=%(rejectURL)s method="POST">
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Comments")%></span></td>
        <td colspan="2"><textarea name="comments" rows="6" cols="50"></textarea></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email Notification")%></span></td>
        <td>
            <input type="checkbox" name="notify" value="true" checked> <%= _("Automatic Email Notification")%>
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td align="left">
            <table align="left">
                <tr>
                    <td align="left">
                        <input type="submit" class="btn" name="reject" value="<%= _("reject")%>">
                    </td>
                    </form>
                    <form action=%(cancelURL)s method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>

