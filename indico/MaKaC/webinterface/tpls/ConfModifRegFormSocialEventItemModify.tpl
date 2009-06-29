<form action=%(postURL)s method="POST">
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"><%= _("Modify a social event")%></td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"><%= _("Caption")%></span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="text" name="caption" size="60" value=%(caption)s>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"><%= _("Number of places")%></span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="text" name="placesLimit" size="60" value="%(placesLimit)s"> <i>(<%= _("use '0' for unlimited")%>)</i>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"><%= _("Maximum of places per participant")%></span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="text" name="maxPlace" size="1" value="%(maxPlace)s"> <i>(<%= _("use '0' in order to disable the selection of places")%>)</i>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"><%= _("Cancel item")%></span></td>
          <td bgcolor="white" class="blacktext" width="100%%">
            <input type="checkbox" name="cancelled" size="60" %(checked)s><%= _("for the following reason")%> 
            <input type="text" name="reason" size="30" value="%(reason)s">
          </td>
        </tr>
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
