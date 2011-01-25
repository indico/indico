<form action=%(postURL)s method="POST">
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"><%= _("Modify a session")%></td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"><%= _("Session")%></span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="text" name="caption" size="60" value=%(caption)s disabled="disabled">
          </td>
        </tr>
        %(billingOptions)s
        <tr>
          <td>&nbsp;</td>
        </tr>
        <tr>
          <td valign="bottom" align="left" colspan="2">
            <input type="submit" class="btn" name="modify" value="<%= _("modify")%>" style="width:80px">
            <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>" style="width:80px">
          </td>
        </tr>
    </table>
</form>
