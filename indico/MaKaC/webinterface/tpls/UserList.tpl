<table class="groupTable" border="0">
<tr>
  <td colspan="2"><div class="groupTitle">${ _("User tools") }</div></td>
</tr>
<tr>
  <td>&nbsp;</td>
  <td class="blacktext"><em>${ _("The database currently hosts %s users.") % nbUsers}</em></td>
</tr>
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Tools")}</span></td>
  <td bgcolor="white" class="blacktext">
    <table>
    <form action="${ createUserURL }" method="POST">
    <tr>
      <td>
        <input type="submit" value="${ _("New User")}" class="btn">
      </td>
    </tr>
    </form>
    <form action="${ mergeUsersURL }" method="POST">
    <tr>
      <td>
        <input type="submit" value="${ _("Merge Users")}" class="btn">
      </td>
    </tr>
    </form>
    <tr>
      <td>
        <input type="button" value="${ _("Log in as ...")}" onclick="loginAs();">
      </td>
    </tr>
    </table>
  </td>
</tr>
<tr>
  <form action="${ browseUsersURL }" method="POST" name="browseForm">
  <input type="hidden" value="" name="letter">
  <td class="dataCaptionTD"><span class="dataCaptionFormat">
     ${ _("Browse Users")}
  </span></td>
  <td bgcolor="white" class="blacktext">
    <span class="groupLink">
    <select name="browseIndex" onChange="this.form.submit();" class="btn">
    ${ browseOptions }
    </select>
    </span>
    ${ browseUsers }
  </td>
  </form>
</tr>

<tr>
  <td colspan="2"><div class="groupTitle">${ _("Search users")}</div></td>
</tr>
<form action="${ searchUsersURL }" method="POST" style="margin:0;">
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Surname")}</span></td>
    <td><input type="text" name="sSurName"></td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("First name")}</span></td>
    <td><input type="text" name="sName"></td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Email")}</span></td>
    <td><input type="text" name="sEmail" size="40"></td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Organisation")}</span></td>
    <td><input type="text" name="sOrganisation"></td>
</tr>
<tr>
    <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Show only active users")}</span></td>
    <td><input type="checkbox" name="onlyActivated"/></td>
</tr>
<tr>
    <td>&nbsp;</td>
    <td><input type="submit" class="btn" value="${ _("apply")}"></input></td>
</tr>
<tr>
    <td>&nbsp;</td>
    <td>
        <table width="100%"><tbody>
            ${ users }
        </tbody></table>
        <br /><br />
    </td>
</tr>

</form>

</table>
