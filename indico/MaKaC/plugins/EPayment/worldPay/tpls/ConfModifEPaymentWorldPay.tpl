<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Title</span></td>
        <td bgcolor="white" width="100%" class="blacktext">${ title }</td>
        <form action=${ dataModificationURL } method="POST">
        <td rowspan="3" valign="bottom" align="right">
            <input type="submit" value="modify">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">URL of worldpay</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ url }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Description</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ description }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">InstID</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ instId }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Test mode</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ testMode }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Accepted Payment response</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ APResponse }</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Cancelled Payment response</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><pre>${ CPResponse }</pre></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
