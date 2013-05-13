<table align="center" width="95%">
<tr>
  <td class="formTitle">${ _("Conference Room Booking")}</td>
</tr>
<tr>
  <td style="padding-left: 20px; padding-top: 20px;">
    <table>
    <tr>
      <td colspan="3" class="groupTitle">${ _("Room Booking Module")}</td>
    </tr>
    <tr>
      <td>
        <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <table width="100%">
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Status")}: </span></td>
              <td>
                <img src="${ iconURL }" style="padding-left: 12px; padding-right: 12px;"/>
                <a href="${urlHandlers.UHRoomBookingModuleActive.getURL()}" rel="no-follow">${ activationText }</a>
              </td>
            </tr>
            </table>
          </td>
        </tr>
        </table>
      </td>
    </tr>
    </table>
    <br /><br />
    <table>
    <tr>
      <td colspan="3" class="groupTitle">${ _("Available Room Booking Plugins")}</td>
    </tr>
    <tr>
      <td>
        <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <table width="100%">
            % for plugin in plugins:
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${plugin.__metadata__['name']}</span></td><td>${plugin.__metadata__['description']}</td>
            </tr>
            % endfor
            </table>
          </td>
        </tr>
        </table>
      </td>
    </tr>
    </table>
    <br /><br />
    <table>
    <tr>
      <td colspan="3" class="groupTitle">${ _("Built-in ZODB Plugin")} </td>
    </tr>
    <tr>
      <td>
        <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            ${ _("You can use the main Indico ZODB backend simply by entering the same Host and Port.")}
            <form action="${ urlHandlers.UHRoomBookingPlugAdminZODBSave.getURL() }" method="post" autocomplete="off">
            <table width="100%">
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${ _("Host")}</span></td>
              <td> &nbsp; <input type="text" value="${ zodbHost }" name="ZODBHost" /></td>
              <td></td>
            </tr>
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${ _("Port")}</span></td>
              <td> &nbsp; <input type="text" value="${ zodbPort }" name="ZODBPort" /></td>
            </tr>
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${ _("Realm")}</span></td>
              <td> &nbsp; <input type="text" value="${ zodbRealm }" name="ZODBRealm" /></td>
            </tr>
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${ _("User")}</span></td>
              <td> &nbsp; <input type="text" value="${ zodbUser }" name="ZODBUser" /></td>
            </tr>
            <tr>
              <td class="titleCellTD"><span class="titleCellFormat">${ _("Password")}</span></td>
              <td> &nbsp; <input type="password" value="${ zodbPassword }" name="ZODBPassword" /></td>
              <td style="text-align: right;"><input type="submit" value="${ _("Save")}" class="btn" /></td>
            </tr>
            </table>
            </form>
          </td>
        </tr>
        </table>
      </td>
    </tr>

    </table>
  </td>
</tr>
</table>
