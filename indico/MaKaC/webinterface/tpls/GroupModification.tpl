<form action="%(postURL)s" method="POST">
  %(locator)s
  <table align="center" width="95%%">
  <tr>
    <td class="formTitle"><a href="%(backURL)s">&lt;&lt; back</a></td>
  </tr>
  <tr>
    <td>
      <br>
      <table width="70%%" align="center" border="0" style="border-left: 1px solid #777777">
      <tr>
        <td colspan="3" class="groupTitle">%(Wtitle)s</td>
      </tr>
      <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">Name</span></td>
	<td align="left"><input type="text" name="name" value="%(name)s"></td>
      </tr>
      <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">email</span></td>
        <td align="left"><input type="text" name="email" value="%(email)s"></td>
      </tr>
      <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">Description</span></td>
        <td align="left"><textarea name="description" cols="43" rows="6">%(description)s</textarea></td>
      </tr>
      <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">Obsolete</span></td>
        <td colspan="2"><input type="checkbox" name="obsolete" <% if obsolete: %> checked="checked" <% end %>></td>
      </tr>
      <tr>
        <td colspan="2" align="center"><input type="submit" class="btn" value="confirm"></td>
      </tr>
      </table>
    </td>
  </tr>
</table>
</form>