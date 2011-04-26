<table align="center" width="100%" class="moveTab"><tr><td>
<form method="POST" action=${ postURL }>
<input type="hidden" name="targetDay" value=${ targetDay }>
<table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
<tr>
  <td colspan="2" class="groupTitle"> ${ _("Move contribution to")}...</td>
</tr>
<tr>
  <td></td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat">${ entryType }</span></td>
  <td bgcolor="white" width="100%" valign="top">&nbsp;
    ${ entryTitle }
  </td>
</tr>
${ autoUpdate }
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Target session")}:</span></td>
  <td style="padding-left:10px">
    <table width="100%">
      ${ targetPlace }
    </table>
  </td>
</tr>
<tr><td>&nbsp;</td></tr>
<tr align="center">
  <td colspan="2" class="buttonBar" valign="bottom" align="center">
    <input type="submit" class="btn" value="${ _("ok")}" name="OK">
    <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL">
  </td>
</tr>
</table>
</form>
</td></tr></table>
