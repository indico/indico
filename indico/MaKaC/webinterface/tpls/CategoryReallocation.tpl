
<form action="${ cancelURL }" method="POST">
<table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
<tr>
  <td class="groupTitle" colspan="2"> ${ _("Re-allocating categories")}</td>
</tr>
<tr>
  <td align="left" colspan="2" bgcolor="white" style="padding-bottom:10px">
     ${ _("Selected categories to be moved")}:
    <ul>${ selectedItems }</ul>
     ${ _("Please, select the destination category where to move the ones mentioned above (use the '+' icon to navigate in the category tree and click on the title of the destination category)")}:<br>
    ${ categTree }
  </td>
</tr>
<tr>
  <td style="border-top:1px solid #777777; padding-top:10px" align="center">
    <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
  </td>
</tr>
</table>
</form>
