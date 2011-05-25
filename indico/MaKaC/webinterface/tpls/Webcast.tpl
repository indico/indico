<table align="center" width="95%">
<tr>
  <td>
    <br>
    <table width="80%" align="left" border="0">
    <tr>
      <td class="groupTitle">${ _("Live channels")}</td>
    </tr>
    <tr>
      <td>
<UL>
  <table width="80%">
  ${ onair }
  </table>
</UL>
      </td>
    </tr>
    </table>
    <br>
    <table width="80%" align="left" border="0" style="padding-top: 20px;">
    <tr>
      <td class="groupTitle">${ _("Forthcoming Webcasts")}</td>
    </tr>
    <tr>
      <td>
<UL>
  <table width="80%">
  ${ webcasts }
  </table>
</UL>
  <form action="${ addwebcastURL }" method="POST">
  <table bgcolor="#bbbbbb" style="margin-left: 10px;">
  <tr bgcolor="#999999"><td colspan=2><font color=white>${ _("New Webcast")}</font>
  </td></tr><tr><td>
  ${ _("event id:")}</td><td><input name="eventid" size=5>
  </td></tr><tr><td colspan=2>
  <input type="submit" name="submit" value="add webcast">
  </td></tr>
  </table>
  </form>
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
<br><br>
