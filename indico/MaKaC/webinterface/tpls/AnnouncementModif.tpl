

<form action="${saveURL}" method="POST" style="margin:0;">

<table class="groupTable">
  <tr>
    <td colspan="2">
      <div class="groupTitle">${ _("Announcement")}</div>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD">
     <span class="dataCaptionFormat">${ _("Text")} : </span>
    </td>
    <td class="blacktext">
      <input type="text" size="70" name="announcement" value="${announcement}">
    </td>
  </tr>
  <tr>
    <td>&nbsp;</td>
    <td class="blacktext">
        <input type="submit" name="Save" value="${ _("Save")}" class="btn">
    </td>
  </tr>
</table>
</from>

