
<table class="groupTable">
<tr>
  <td colspan="5"><div class="groupTitle"><%= _("Access control")%></div></td>
</tr>
<tr>
  <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Current status")%></span></td>
  <td class="blacktext">
    <form action="%(setVisibilityURL)s" method="POST">
    %(locator)s
    <b>%(privacy)s</b><br/>
    <small>
    %(changePrivacy)s
    </small>
    </form>
  </td>
</tr>
<tr>
  <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Users allowed to access")%></span></td>
  <td class="blacktext">%(userTable)s</td>
</tr>
</table>

