
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">${ title }</td>
        <form action=${ dataModificationURL } method="POST">
        <td rowspan="3" valign="bottom" align="right">
            <input type="submit" value="${ _("modify")}">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("URL of yellowpay")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ url }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Master Shop ID")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ mastershopid }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Shop ID")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ shopid }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Hash Seed")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ hashseed }</pre></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
