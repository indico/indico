<form action=${ postURL } method="POST">
<br>
<table width="60%" align="center" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
  <tr>
    <td nowrap class="groupTitle" colspan="2"><b>${ _("Modifying") } ${ title }</b></td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">* </font>${ _("Arrival date")}</span></td>
    <td align="left" width="100%">&nbsp; ${ arrivalDate }</td>
  </tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">* </font>${ _("Departure date")}</span></td>
    <td align="left" width="100%">&nbsp;${ departureDate }</td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">* </font>${ _("Accommodation type")}</span></td>
    <td align="left" width="100%">&nbsp;
      <table>
        ${ accommodationTypes }
      </table>
    </td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td align="left" colspan="2">
      <input type="submit" class="btn" name="modify" value="${ _("modify")}">
      <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
    </td>
  </tr>
</table>
