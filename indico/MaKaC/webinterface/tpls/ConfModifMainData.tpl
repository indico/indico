<div class="management-page">
    <header>
        <div class="title">
            <h2>${ _("General Settings")}</h2>
        </div>
    </header>
    <table class="groupTable">
            <%include file="EventModifMainData.tpl" args="evtType='conference', confObj=self_._conf"/>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Screen dates")}</span></td>
            <td class="blacktext">${screenDates}</td>
            <td align="right" valign="bottom">
            <form action="${screenDatesURL}" method="POST">
                <input type="submit" class="btn" value="${ _("modify")}">
            </form>
            </td>
        </tr>
        <tr>
            <td colspan="3" class="horizontalLine">&nbsp;</td>
        </tr>
    </table>
</div>

<script type="text/javascript">
function removeItem(number, form)
{
    form.selChair.value = number;
    form.submit();
}
</script>
