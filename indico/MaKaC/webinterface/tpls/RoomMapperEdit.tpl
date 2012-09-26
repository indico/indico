<form action="${ postURL }" method="POST">
${ locator }
<table align="center" width="95%">
<tr>
  <td class="formTitle"> ${ _("Room Mappers")}</td>
</tr>
<tr>
  <td>
    <br>
    <table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle"> ${ _("Modifying Room Mapper")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Room Mapper name")}</span></td>
      <td><input type="text" name="name" size="45" value="${ name }"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
      <td><textarea name="description" cols="44" rows="3">${ description }</textarea></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Place name to match the location with")}<br><small>${ _("(e.g. CERN)")}</small></span></td>
      <td><input type="text" name="placeName" size="45" value="${ placeName }"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Regular expressions to match room with")}<br><br><small>${ _("enter each regular expression in a new line.")}</small></span></td>
      <td><textarea name="regexps" rows="4" cols="44">${ regexps }</textarea></td>
      <td style="font-size: 11px; padding-left: 5px; padding-top: 5px; color: #999; vertical-align: top;">${ _("Every named group from regular expression will be put to corresponding value name in the Map URL field.")}<td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Map URL")}<br><small>${ _("(e.g. http://www.example.com/map?go=['{building}-{floor}-{roomNr}'])")}</small></span></td>
      <td><input type="text" name="url" size="45"  value="${ url }"></td>
    </tr>
    <% from MaKaC.common import filters, info %>
    <% minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance() %>
    % if minfo.getRoomBookingModuleActive():
      <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"></td>
        <td style="color: #8F1122">${_("Room booking module is enabled so you have to use specific group names in Map URL field: {building}, {floor} and {roomNr}. If you do not use them Room Mapper will not work for rooms from Room booking module.")}</td>
      </tr>
    % endif
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" name="OK" value="${ _("ok")}"></td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
