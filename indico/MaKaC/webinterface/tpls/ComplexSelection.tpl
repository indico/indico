
<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
<tr>
  <td colspan="3" class="groupTitle">%(WPtitle)s</td>
</tr>
<tr>
<form action="%(postURL)s" method="POST">
  <td>
    <table>
    <tr>
      <td rowspan="4" valign="middle" align="left" style="border-right:1px solid #5294CC"><img src=%(usericon)s/></td>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Family name")%></span></td>
      <td bgcolor="white" width="100%%">
        <input type="text" name="surname" size="60" value="%(surName)s">
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("First name")%></span></td>
      <td bgcolor="white" width="100%%">
        <input type="text" name="firstname" size="60" value="%(firstName)s">
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
      <td bgcolor="white" width="100%%">
        <input type="text" name="email" size="60" value="%(email)s">
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Organisation")%></span></td>
      <td bgcolor="white" width="100%%">
        <input type="text" name="organisation" size="60" value="%(organisation)s">
      </td>
    </tr>
    </table>
  </td>
  <td valign="top" rowspan="4" align="right">
  <input type="submit" class="btn" value="<%= _("search")%>" name="action">
  %(searchOptions)s
</form>
  </td>

  %(msg)s
  <form action="%(addURL)s" method="POST">
<tr>
  <td bgcolor="white" colspan="3">
    %(params)s
    %(searchResultsTable)s
  </td>
  <td>
    %(selectionBox)s
  </td>
</tr>
</form>
<tr>
  <td colspan="3" align="center">
    <form action="%(cancelURL)s" method="POST">
    %(params)s
    <input type="submit" class="btn" value="<%= _("select")%>">
    <input type="submit" class="btn" value="<%= _("cancel")%>">
    </form>
  </td>
</tr>
</table>

