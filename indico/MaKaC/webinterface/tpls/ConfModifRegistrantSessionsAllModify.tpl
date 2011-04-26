<form action=${ postURL } method="POST">
<br>
<table width="60%" align="center" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
  <tr>
    <td nowrap class="groupTitle" colspan="2"><b>${ _("Modifying") } ${ title }</b></td>
  </tr>
  <tr><td><br></td></tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Selected sessions")}</span></td>
    <td width="100%" align="left" style="padding-left:10px">${ sessions }</td>
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
