<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>


<table width="100%" border="0">
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ enableDisable }</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
        <table>
            <tr>
                <td>${features}</td>
            </tr>
        </table>
      </td>
      <td valign="top">
        <form action="${ ITInfoModifURL }" method="GET">
        <input type="submit" class="btn" value="${ _("modify")}">
        </form>
      </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Contact person name")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">${instanceTrackingContact}</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Contact email address")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">${instanceTrackingEmail}</td>
    </tr>
</table>
