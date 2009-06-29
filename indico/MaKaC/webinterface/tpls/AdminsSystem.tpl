<table align="center" width="95%%">
<tr>
  <td>
    <br>
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle"><%= _("System configuration")%></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Proxy")%></span></td>
      <td bgcolor="white" width="100%%" valign="top" class="blacktext"><%= ("No", "yes")[minfo.useProxy()] %></td>
      <td rowspan="4" valign="top">
        <form action="%(ModifURL)s" method="POST">
        <input type="submit" class="btn" value="modify">
        </form>
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
