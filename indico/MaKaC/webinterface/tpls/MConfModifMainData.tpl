<table width="100%">
    <%include file="EventModifMainData.tpl" args="evtType='meeting', confObj=self_._conf"/>
    % if Config.getInstance().getReportNumberSystems():
    <tr>
        <td class="dataCaptionTD"><a name="reportNumber"></a><span class="dataCaptionFormat">Report numbers</span></td>
        <td colspan="2" class="blacktext">${ reportNumbersTable }</td>
    </tr>

    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    % endif
</table>
