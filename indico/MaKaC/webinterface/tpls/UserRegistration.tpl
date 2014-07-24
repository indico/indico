<% from indico.util.i18n import getLocaleDisplayNames %>
<center>
<form action=${ postURL } method="POST">
${ locator }
<table width="80%">
<tr>
  <td colspan="2" align="center"><font size="+2"><u>${ Wtitle }</u></font></td>
</tr>
<tr>
  <td colspan="2" align="center">
    <table width="90%">
    <tr>
      <td>
        <font color="gray">
         ${ _("To create a new user please fill in the following form.")}<br>
        ${ after }<br><br>
        </font>
        <font color="red">
          <center><b> ${ _("Beware! This is not a conference registration form but an Indico account creation.")}</b></center><br><br>
        </font>
      </td>
    </tr>
    </table>
    ${ msg }
  </td>
</tr>
<tr>
  <td colspan="2"><b> ${ _("Personal data")}</b></td>
</tr>
<tr>
  <td colspan="2" bgcolor="black"></td>
</tr>
<tr>
  <td align="right">
    <font color="gray"> ${ _("Title")}</font>
  </td>
  <td align="left">
    <select name="title">
    ${ titleOptions }
    </select>
  </td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Family name")}</font></td>
  <td align="left"><input type="text" name="surName" value=${ surName } size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("First name")}</font></td>
  <td align="left"><input type="text" name="name" value=${ name } size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Affiliation")}</font></td>
  <td align="left"><input type="text" name="organisation" value=${ organisation } size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Email")}</font></td>
  <td align="left"><input type="text" name="email" value=${ email } size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Language")}</font></td>
  <td bgcolor="white" width="100%" align="left">
  <select size=1 name="lang">
    % for l in getLocaleDisplayNames():
        <option value="${l[0]}" ${'selected="selected"' if l[0]==defaultLang else ""}>${l[1]}</option><br>
    % endfor
  </select>
  </td>
</tr>
<tr>
  <td align="right" valign="top"><font color="gray"> ${ _("Address")}</font></td>
  <td align="left"><textarea name="address" rows="5" cols="75">${ address }</textarea></td>
</tr>
<tr>
  <td align="right" nowrap><font color="gray"> ${ _("Telephone number")}</font></td>
  <td align="left"><input type="text" name="telephone" value=${ telephone } size="25"></td>
</tr>
<tr>
  <td align="right"><font color="gray"> ${ _("Fax number")}</font></td>
  <td align="left"><input type="text" name="fax" value=${ fax } size="25"></td>
</tr>
<!-- Fermi timezone awareness -->
<tr>
 <td align="right">
     <font color="gray">${ _("My Timezone")}</font>
 </td>
    <td bgcolor="white" width="100%" align="left">
       <select name="timezone">${ timezoneOptions }</select>
    </td>
</tr>
<tr>
 <td align="right">
     <font color="gray">${ _("Display Timezone")}</font>
 </td>
    <td bgcolor="white" width="100%" align="left">
       <select name="displayTZMode">option value=${ displayTZModeOptions }</select>
    </td>
</tr>
<!-- Fermi timezone awareness(end) -->
<tr>
  <td colspan="2">
    <center><font color="red">${ _("You must enter a valid email address. An email will be sent to you to confirm the registration.")}</font></center>
    <br><b>${ _("Account data")}</b>
</tr>
<tr>
  <td colspan="2" bgcolor="black"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Login")}</font></td>
  <td align="left"><input type="text" name="login" value=${ login } size="25"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> ${ _("Password")}</font></td>
  <td align="left"><input type="password" name="password" value="" size="25"></td>
</tr>
<tr>
  <td align="right" nowrap><font color="gray"><font color="red">* </font> ${ _("Password (again)")}</font></td>
  <td align="left"><input type="password" name="passwordBis" value="" size="25"></td>
</tr>
<tr>
  <td colspan="2" align="center">
    <br><b> ${ _("""Please note that fields marked with <font color="red">*</font> are mandatory.""")}</b><br>
    <br><input type="submit" class="btn" name="Save" value="${ _("confirm")}">
  </td>
</tr>
</table>
<br>
</form>
</center>
