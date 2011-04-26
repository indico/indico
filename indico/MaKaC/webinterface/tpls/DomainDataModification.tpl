<form action="${ postURL }" method="POST">
${ locator }
<table align="center" width="95%">
<tr>
  <td class="formTitle">${ _("Domains")}</td>
</tr>
<tr>
  <td>
    <br>
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle">${ _("Modifying DOMAIN")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Name")}</span></td>
      <td align="left" width="80%"><input type="text" name="name" value="${ name }" size="25"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Description")}</span></td>
      <td align="left"><textarea name="description" cols="43" rows="6">${ description }</textarea></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("IP Filter")}<br><br><small>${ _('Enter the IP filters<br>separated by ";"')}</small></span></td>
      <td align="left"><textarea name="filters" rows="2" cols="30">${ filters }</textarea></td>
    </tr>
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" name="OK" value="${ _("ok")}"></td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
