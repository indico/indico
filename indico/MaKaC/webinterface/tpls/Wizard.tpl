<% from indico.util.i18n import getLocaleDisplayNames %>
<form action="" method="POST">
  <center>
    <table width="80%">
      <tbody>
        <tr>
          <td colspan="2" align="center">
            <font size="+2">
                <u>${ _("Admin Creation Wizard")}</u>
            </font>
          </td>
        </tr>
        <tr>
          <td colspan="2" height="80em">
            ${msg}
          </td>
        </tr>

        <tr>
          <td colspan="2">
            <b>${ _("1. User creation")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="2" bgcolor="black"></td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("First name")}</font>
          </td>
          <td align="left">
            <input type="text" name="name" value=${ name }>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Family name")}</font>
          </td>
          <td align="left">
            <input type="text" name="surName" value=${ surName }>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Email")}</font>
          </td>
          <td align="left">
            <input type="text" name="userEmail" value=${ userEmail }>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Login")}</font>
          </td>
          <td align="left">
            <input type="text" name="login" value=${ login }>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Password")}</font>
          </td>
          <td align="left">
            <input type="password" name="password" value="">
          </td>
        </tr>
        <tr>
          <td align="right" nowrap>
            <font color="gray"> ${ _("Password (again)")}</font>
          </td>
          <td align="left">
            <input type="password" name="passwordBis" value="">
          </td>
        </tr>
        <tr>
          <td colspan="2" height="20em"></td>
        </tr>

        <tr>
          <td colspan="2">
            <b>${ _("2. Server Settings")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="2" bgcolor="black"></td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray">${ _("Language")}</font>
          </td>
          <td bgcolor="white" width="100%" align="left">
            <select size=1 name="lang">
                <script type='text/javascript'>
                  var lang = navigator.language || navigator.userLanguage;
                  var selected;
                  % for l in getLocaleDisplayNames():
                    selected = '';
                    if ('${l[0]}'.split('_')[0] == lang.split('-')[0])
                      selected = ' selected';
                    document.write('<option value="${l[0]}"'+selected+'>${l[1]}</option>');
                  % endfor
                </script>
            </select>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray">${ _("Timezone")}</font>
          </td>
          <td bgcolor="white" width="100%" align="left">
            <select name="timezone">${ timezoneOptions }</select>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Organisation")}</font>
          </td>
          <td align="left">
            <input type="text" name="organisation" value=${organisation}>
          </td>
        </tr>
        <tr>
          <td colspan="2" height="20em">
        </tr>

        <tr>
          <td colspan="2">
            <b>${ _("3. Instance tracking")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="2" bgcolor="black"></td>
        </tr>
        <tr>
          <td colspan="2" align="left">
            <table width="90%">
              <tr>
                <td>
                  <font color="gray">
                    ${_("By accepting the Instance Tracking Terms you accept:")}
                    <ul>
                      <li>${ _("sending anonymous statistic data to Indico@CERN;")}</li>
                      <li>${ _("receiving security warnings from the Indico team;")}</li>
                      <li>${ _("receiving a notification when a new version is released.")}</li>
                    </ul>
                    ${_("Please note that no private information will ever be sent to Indico@CERN and that you will be able to change the Instance Tracking settings anytime in the future (from Server Admin, General Settings).")}
                  </font>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Accept")}</font>
          </td>
          <td align="left">
            <input type="checkbox" name="accept" value="${ _("checked")}" ${checked}>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Email")}</font>
          </td>
          <td align="left">
            <input type="text" name="instanceTrackingEmail" value=${instanceTrackingEmail}>
          </td>
        </tr>
        <tr>
          <td colspan="2" height="20em"></td>
        </tr>

        <tr>
          <td colspan="2" align="center">
            <input type="submit" class="btn" name="save" value="${ _("confirm")}">
          </td>
        </tr>

      </tbody>
    </table>
  </center>
</form>
