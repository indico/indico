<div class="groupTitle">${ _("General Admin Data")} - ${ _("Modify System General Information")}</div>

<form action="${ postURL }" method="POST">
  <table>
    <tr>
      <td nowrap class="titleCellTD">
        <span class="titleCellFormat">${ _("Proxy")}</span>
      </td>
      <td bgcolor="white" width="100%">&nbsp;
        <input type="checkbox" size="50" name="proxy" value="True" ${ ("", "checked")[minfo.useProxy()] } />
        <small>${ _("Check this if users access Indico via proxy (load balancing)")}</small>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD">
        <span class="titleCellFormat">${ _("Archiving Volume")}</span>
      </td>
      <td bgcolor="white" width="100%">&nbsp;
        <input type="text" size="50" name="volume" value="${ minfo.getArchivingVolume() }" />
      </td>
    </tr>
    <tr>
      <td colspan="2" align="center">
        <table align="center">
        <tr>
          <td>
            <input type="submit" class="btn" name="action" value="${ _('OK')}">
          </td>
          <td>
            <input type="submit" class="btn" name="action" value="${ _('Cancel')}">
          </td>
        </tr>
        </table>
      </td>
    </tr>
  </table>
</form>
