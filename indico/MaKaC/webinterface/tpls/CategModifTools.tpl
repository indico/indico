
<table class="groupTable">
<tr>
  <td><div class="groupTitle">${ _("Common actions")}</div></td>
</tr>
<tr>
  <td bgcolor="white" width="100%" style="padding-top:10px">
        <form action="${ deleteCategoryURL }" method="POST">
        ${ deleteButton }
        <input type="hidden" name="selectedCateg" value="${ id }">
        </form>
  </td>
</tr>
</table>
