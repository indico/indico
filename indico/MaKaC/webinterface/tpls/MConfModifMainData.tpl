<div class="management-page">
    <header>
        <div class="title">
            <h2>${ _("General Settings")}</h2>
        </div>
    </header>
    <table width="100%">
        <%include file="EventModifMainData.tpl" args="evtType='meeting', confObj=self_._conf"/>
        <tr>
            <td class="dataCaptionTD"><a name="reportNumber"></a><span class="dataCaptionFormat">External IDs</span></td>
            <td colspan="2" class="blacktext">
                ${ template_hook('event-references-list', event=self_._conf.as_event) }
            </td>
        </tr>

        <tr>
            <td colspan="3" class="horizontalLine">&nbsp;</td>
        </tr>
    </table>
</div>
