<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" class="blacktext">
            %(title)s
        </td>
		<form action=%(dataModificationURL)s method="POST">
        <td rowspan="5" valign="bottom" align="right" width="1%%">
                <input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Place")%></span></td>
        <td bgcolor="white" class="blacktext">%(place)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Start date")%></span></td>
        <td bgcolor="white" class="blacktext">%(startDate)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> <%= _("End date")%></span></td>
        <td bgcolor="white" class="blacktext">%(endDate)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Duration")%></span></td>
        <td bgcolor="white" class="blacktext">%(duration)s</td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>            
