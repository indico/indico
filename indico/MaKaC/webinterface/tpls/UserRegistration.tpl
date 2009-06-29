<%! from MaKaC.i18n import _,langList %>
<center>
<form action=%(postURL)s method="POST">   
%(locator)s
<table width="80%%">
<tr>
  <td colspan="2" align="center"><font size="+2"><u>%(Wtitle)s</u></font></td>
</tr>
<tr>
  <td colspan="2" align="center">
    <table width="90%%">
    <tr>
      <td>
        <font color="gray">
         <%= _("To create a new user please fill in the following form.")%><br>
        %(after)s<br><br>
        </font>
        <font color="red">
          <center><b> <%= _("Beware! This is not a conference registration form but an Indico account creation.")%></b></center><br><br>
        </font>
      </td>
    </tr>
    </table>
    %(msg)s
  </td>
</tr>
<tr>
  <td colspan="2"><b> <%= _("Personal data")%></b></td>
</tr>
<tr>
  <td colspan="2" bgcolor="black"></td>
</tr>
<tr>
  <td align="right">
    <font color="gray"> <%= _("Title")%></font>
  </td>
  <td align="left">
    <select name="title">
    %(titleOptions)s
    </select>
  </td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Family name")%></font></td>
  <td align="left"><input type="text" name="surName" value=%(surName)s size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("First name")%></font></td>
  <td align="left"><input type="text" name="name" value=%(name)s size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Affiliation")%></font></td>
  <td align="left"><input type="text" name="organisation" value=%(organisation)s size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Email")%></font></td>
  <td align="left"><input type="text" name="email" value=%(email)s size="100"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Language")%></font></td>
  <td bgcolor="white" width="100%%" align="left">
  <select size=1 name="lang">
    <% for l in langList(): %>
		<option value="<%=l[0]%>" <%if l[0]==defaultLang: %>selected="selected"<%end%>><%=l[1]%></option><br>
	<% end %>
  </select>
  </td>
</tr>
<tr>
  <td align="right" valign="top"><font color="gray"> <%= _("Address")%></font></td>
  <td align="left"><textarea name="address" rows="5" cols="75">%(address)s</textarea></td>
</tr>
<tr>
  <td align="right" nowrap><font color="gray"> <%= _("Telephone number")%></font></td>
  <td align="left"><input type="text" name="telephone" value=%(telephone)s size="25"></td>
</tr>
<tr>
  <td align="right"><font color="gray"> <%= _("Fax number")%></font></td>
  <td align="left"><input type="text" name="fax" value=%(fax)s size="25"></td>
</tr>
<!-- Fermi timezone awareness -->
<tr>
 <td align="right">
     <font color="gray"><%= _("My Timezone")%></font>
 </td>
    <td bgcolor="white" width="100%%" align="left">
       <select name="timezone">%(timezoneOptions)s</select>
    </td>
</tr>
<tr>
 <td align="right">
     <font color="gray"><%= _("Display Timezone")%></font>
 </td>
    <td bgcolor="white" width="100%%" align="left">
       <select name="displayTZMode">option value=%(displayTZModeOptions)s</select>
    </td>
</tr>
<!-- Fermi timezone awareness(end) -->
<tr>
  <td colspan="2">
    <center><font color="red"><%= _("You must enter a valid email address. An email will be sent to you to confirm the registration.")%></font></center>
    <br><b><%= _("Account data")%></b>
    <br><%= _("Please note that your password will be stored in clear text in our database which will allow us to send it back to you in case you lost it. Try avoid using the same password as accounts you may have in other systems.")%>
  </td>
</tr>
<tr>
  <td colspan="2" bgcolor="black"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Login")%></font></td>
  <td align="left"><input type="text" name="login" value=%(login)s size="25"></td>
</tr>
<tr>
  <td align="right"><font color="gray"><font color="red">* </font> <%= _("Password")%></font></td>
  <td align="left"><input type="password" name="password" value="" size="25"></td>
</tr>
<tr>
  <td align="right" nowrap><font color="gray"><font color="red">* </font> <%= _("Password (again)")%></font></td>
  <td align="left"><input type="password" name="passwordBis" value="" size="25"></td>
</tr>
<tr>
  <td colspan="2" align="center">
    <br><b> <%= _("""Please note that fields marked with <font color="red">*</font> are mandatory.""")%></b><br>
    <br><input type="submit" class="btn" name="Save" value="<%= _("confirm")%>">
  </td>
</tr>
</table>
<br>
</form>
</center>
