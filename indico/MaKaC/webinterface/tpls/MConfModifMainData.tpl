<table width="100%">
	<% includeTpl('EventModifMainData', evtType='meeting', confObj=self._conf) %>
    <tr>
        <td class="dataCaptionTD"><a name="reportNumber"></a><span class="dataCaptionFormat">Report numbers</span></td>
        <td colspan="2" class="blacktext"><%= reportNumbersTable %></td>
    </tr>

	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>