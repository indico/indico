<table align="center" width="95%">
<tr>
  <td class="formTitle"><a href="<%=backURL%>">&lt;&lt; back</a></td>
</tr>
<tr>
  <td>
    <br>
    <table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle">
        Group <b><%=name%></b><br>
      </td>
    </tr>
    <tr>
      <td colspan="2" bgcolor="white" width="100%" valign="top" class="blacktext">
        <table width="100%">
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">Description</span></td>
          <td><%=description%></td>
        </tr>
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">Email</span></td>
          <td><%=email%></td>
        </tr>
        <tr>
          <td nowrap class="titleCellTD"><span class="titleCellFormat">Obsolete</span></td>
          <td><%= obsolete %></input></td>
        </tr>
        </table>
      </td>
      <form action="<%=modifyURL%>" method="POST">
      <td valign="top" align="right">
	<input type="submit" class="btn" value="modify"><br>
      </td>
      </form>
    </tr>
    </table>
  </td>
</tr>
<tr>
  <td>
    <br>
    <table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle">Members</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
	<%=membersList%>
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>