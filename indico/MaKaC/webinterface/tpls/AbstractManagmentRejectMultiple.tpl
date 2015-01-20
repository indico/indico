<script type="text/javascript">

function showAbstracts()
{
    var listOfAbstracts = ${ listOfAbstracts };
    var ul = Html.ul({id: '',style:{listStyle: 'circle', marginLeft:'-25px'}});
    for (var i = 0; i < listOfAbstracts.length; i++)
    {
        ul.append(Html.li('', listOfAbstracts[i]));
    }
    var popup = new AlertPopup("List of abstracts", ul);
    popup.open();
}

</script>

<div class="groupTitle">${ _("Rejecting %s abstracts")%abstractsQuantity }</div>
<em>${ _("Click")} <a href="javascript:showAbstracts()">${ _("here") }</a> ${_("to see the list of the abstracts you are rejecting")}</em>
<br/><br/>
<table width="100%" align="center" border="0">
    <tr>
        <form action=${ rejectURL } method="POST">
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Comments")}</span></td>
        <td colspan="2"><textarea name="comments" rows="6" cols="50"></textarea></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email Notification")}</span></td>
        <td>
            <input type="checkbox" name="notify" value="true" checked> ${ _("Automatic Email Notification")}
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td align="left">
            <table align="left">
                <tr>
                    <td align="left">
                        <input type="submit" class="btn" name="reject" value="${ _("reject")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
