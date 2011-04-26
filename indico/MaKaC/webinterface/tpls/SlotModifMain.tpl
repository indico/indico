<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
        <td bgcolor="white" class="blacktext">
            ${ title }
        </td>
        <form action=${ dataModificationURL } method="POST">
        <td rowspan="5" valign="bottom" align="right" width="1%">
                <input type="submit" class="btn" value="${ _("modify")}">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Place")}</span></td>
        <td bgcolor="white" class="blacktext">${ place }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Start date")}</span></td>
        <td bgcolor="white" class="blacktext">${ startDate }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> ${ _("End date")}</span></td>
        <td bgcolor="white" class="blacktext">${ endDate }</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Duration")}</span></td>
        <td bgcolor="white" class="blacktext">${ duration }</td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
