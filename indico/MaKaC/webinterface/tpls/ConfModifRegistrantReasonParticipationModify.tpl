<form action=${ postURL } method="POST">
<br>
<table width="60%" align="center" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
  <tr>
    <td nowrap class="groupTitle" colspan="2"><b>${ _("Modifying") } ${ title }</b></td>
  </tr>
  <tr><td><br></td></tr>
  <tr>
    <td align="left" valign="top"><span class="titleCellFormat">&nbsp;${ _("Reason")}</span><br><br>
    &nbsp;&nbsp;<textarea name="reason" rows="5" cols="75">${ reasonParticipation }</textarea></td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td align="left" colspan="2">
      <input type="submit" class="btn" name="modify" value="${ _("modify")}">
      <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
    </td>
  </tr>
</table>
<br>
</form>
