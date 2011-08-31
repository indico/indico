<table align="center" width="95%">
<tr>
  <td>
    <br />
    <table width="80%" align="left" border="0">
    <tr>
      <td class="groupTitle">Channels</td>
    </tr>
    <tr>
      <td>
  ${ channels }
  <form action="${ postURL }" method="POST">
  <table bgcolor="#bbbbbb">
  <tr bgcolor="#999999"><td colspan=2><font color=white>${ _("New Channel")}</font>
  </td></tr><tr><td>
  ${ _("name:")}</td><td><input name="chname" size=30>
  </td></tr><tr><td>
  ${ _("url:")}</td><td><input name="churl" size=30>
  </td></tr><tr><td>
  ${ _("width")}:</td><td><input name="chwidth" size=4>
  </td></tr><tr><td>
  ${ _("height:")}</td><td><input name="chheight" size=4>
  </td></tr><tr><td colspan=2>
  <input type="submit" name="submit" value="add channel">
  </td></tr>
  </table>
  </form>
      </td>
    </tr>
    </table>

    <br /><br />

    <table width="80%" align="left" border="0" style="padding-top:20px;">
    <tr>
      <td class="groupTitle">${ _("Webcast Synchronization")}</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%" valign="top" class="blacktext" style="padding-top: 10px;">
        <form action="${ saveWebcastSynchronizationURL }" method="POST">
          <span>${ _("Synchronization URL: ")}</span>
          <input name="webcastSynchronizationURL" size="50" value="${ webcastSynchronizationURL }"/>
          <input type="submit" name="submit" value="Save">
        </form>
        <div style="padding-top: 10px;padding-bottom: 10px;">
          ${ _("Used to automatically synchronize every time:")}
          <ul style="padding:0;margin:0;margin-left: 50px;">
              <li>
                  ${ _("Something in the \"Live channels\" section is changed.")}
              </li>
              <li>
                  ${ _("An event is added or removed from \"Forthcoming webcasts\"")}
              </li>
          </ul>
          ${ _("Leave empty for no automatic synchronization.")}
        </div>
        <form action="${ webcastManualSynchronize }" method="POST">
            <input type="submit" name="submit" value="Synchronize manually">
            <span>${ _("Remember to save the URL first if you have modified it.")}</span>
        </form>
      </td>
    </tr>
    </table>

    <br /><br />

    <table width="80%" align="left" border="0" style="padding-top:20px;">
    <tr>
      <td class="groupTitle">${ _("Webcast Administrators list")}</td>
    </tr>
    <tr>
        <table width="100%">
            <tr>
                <td bgcolor="white" width="60%">
                    <table width="100%">
                        <tr>
                            <td><ul id="inPlaceWebcastAdmin" class="UIPeopleList"></ul></td>
                        </tr>
                        <tr>
                            <td nowrap style="width:60%; padding-top:5px;">
                                <input type="button" onclick="webcastAdminListManager.addExistingUser();" value='${ _("Add webcast administrator") }'></input>
                            </td>
                            <td></td>
                        </tr>
                    </table>
                </td>
            </tr>
       </table>
    </tr>
    </table>
  </td>
</tr>
</table>
<br /><br />

<script>

var webcastAdminListManager = new ListOfUsersManager(null,
        {'addExisting': 'admin.services.addWebcastAdministrators', 'remove': 'admin.services.removeWebcastAdministrator'},
        {}, $E('inPlaceWebcastAdmin'), "webcast administrator", "UIPerson", false, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ webcastAdmins | n,j});

</script>
