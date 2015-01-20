<div class="groupTitle">${ _("Room Mapper for <small>%s</small> ") % name } </div>
<table>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ description }</td>
  </tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Place name to match the location with")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ placeName }</td>
  </tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Regular expressions to match the room with")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
      <ul>
        % for exp in regexps:
        <li>${ exp | h }</li>
        % endfor
      </ul>
    </td>
  </tr>
  <tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Map URL")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">${ url }</td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <form action="${ modifyURL }" method="POST">
        <input type="submit" class="btn" value="${ _("modify")}" />
      </form>
    </td>
  </tr>
</table>
