<div class="groupTitle">${ _("System Configuration")}</div>
<table>
  <tr>
    <td nowrap class="titleCellTD">
      <span class="titleCellFormat">${ _("Proxy")}</span>
    </td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
      ${ ("No", "Yes")[minfo.useProxy()] }
    </td>
    <td rowspan="4" valign="top">
      <form action="${ ModifURL }" method="POST">
      <input type="submit" class="btn" value="${ _("Modify")}">
      </form>
    </td>
  </tr>
  <tr>
    <td nowrap class="titleCellTD">
      <span class="titleCellFormat">${ _("Archiving Volume")}</span>
    </td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
      ${ minfo.getArchivingVolume() }
    </td>
  </tr>
</table>
