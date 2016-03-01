<table width="100%">
    <div class="management-page">
        <%include file="EventModifMainData.tpl" args="evtType='meeting', confObj=self_._conf"/>
        % if Config.getInstance().getReportNumberSystems():
        <tr>
            <td class="dataCaptionTD"><a name="reportNumber"></a><span class="dataCaptionFormat">External IDs</span></td>
            <td colspan="2" class="blacktext">
                ${ template_hook('event-references-list', event=self_._conf.as_event) }
            </td>
        </tr>

        <tr>
            <td colspan="3" class="horizontalLine">&nbsp;</td>
        </tr>
        % endif
    </div>
</table>
