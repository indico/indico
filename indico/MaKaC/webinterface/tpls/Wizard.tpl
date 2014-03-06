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
            <font color="gray"> ${ _("Affiliation")}</font>
          </td>
          <td align="left">
            <input type="text" name="organisation" value=${ organisation }>
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
          <td>Explanation</td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Email")}</font>
          </td>
          <td align="left">
            <input type="text" name="institutionEmail" value=${ institutionEmail }>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Institution")}</font>
          </td>
          <td align="left">
            <input type="text" name="institution" value=${ institution }>
          </td>
        </tr>
        <tr>
          <td>Buttons...</td>
        </tr>
        <tr>
          <td colspan="2" height="20em"></td>
        </tr>

        <tr>
          <td colspan="2" align="center">
            <input type="submit" class="btn" name="Save" value="${ _("confirm")}">
          </td>
        </tr>

      </tbody>
    </table>
  </center>
</form>
