<form action="${ postURL }" method="POST">
${ locator }
<table align="center" width="95%">
<tr>
  <td class="formTitle"> ${ _("Room Mappers")}</td>
</tr>
<tr>
  <td>
    <br>
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle"> ${ _("Modifying Room Mapper")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
      <td align="left" width="80%"><input type="text" name="name" size="54" value="${ name }"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
      <td align="left"><textarea name="description" cols="40" rows="6">${ description }</textarea></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("URL")}</span></td>
      <td align="left" width="80%"><input type="text" name="url" size="54"  value="${ url }"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Place Name to match with<br><small>(e.g. CERN)</small>")}</span></td>
      <td align="left" width="80%"><input type="text" name="placeName" size="54" value="${ placeName }"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Regular Expressions<br><br><small>enter each regular<br>expression in a new line.")}</small></span></td>
      <td align="left"><textarea name="regexps" rows="2" cols="40">${ regexps }</textarea></td>
    </tr>
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" name="OK" value="${ _("ok")}"></td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
