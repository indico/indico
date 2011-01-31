<table class="groupTable">
<tr>
  <td colspan="2"><div class="groupTitle"><%= _("Domain control")%></div></td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Allowed domains")%><br><font size="-2">(<%= _("if no domain is selected<br>no control is applied")%>)</font></span></td>
  <td class="blacktext">
    <form action="<%= removeURL %>" method="POST">
    <%= locator %>
    <table width="100%">
    <tr>
      <td width="80%">
        <%= domains %>
      </td>
      <td width="20%" align="right" valign="bottom">
        <table>
        <tr>
          <td>
            <input type="submit" class="btn" value="<%= _("remove")%>">
          </td>
          <td>
            <select name="addDomain">
            <option><%= _("Select")%>:
            <%= domainsToAdd %>
            </select>
          </td>
          <td>
            <input type="submit" class="btn" value="<- <%= _("add")%><" onClick="if (this.form.addDomain.value=='<%= _("Select")%>:') { return false; } else { this.form.action='<%= addURL %>'; }">
          </td>
        </tr>
        </table>
      </td>
    </tr>
    </table>
    </form>
  </td>
</tr>
</table>