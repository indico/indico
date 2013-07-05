<br />
<table width="90%" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Code")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">${ code }</td>
        <form action=${ dataModificationURL } method="POST">
        <td rowspan="3" valign="bottom" align="right">
            <input type="submit" class="btn" value="${ _("modify")}">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext"><b>${ title }</b></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            ${ description }
        </td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<br />
