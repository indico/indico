
<table class="groupTable">
<tr>
  <td><div class="groupTitle"><%= _("Common actions")%></div></td>
</tr>
<tr>
  <td bgcolor="white" width="100%%" style="padding-top:10px">
        <form action="%(deleteCategoryURL)s" method="POST">
        %(deleteButton)s
        <input type="hidden" name="selectedCateg" value="%(id)s">
        </form>
        %(clearCache)s
  </td>
</tr>
</table>
