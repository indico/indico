<form action="<%=urlHandlers.UHAdminsStyles.getURL()%>" method="POST">
<table align="center" width="95%%">
<tr>
  <td class="formTitle"><a href="<%=urlHandlers.UHAdminsStyles.getURL()%>">&lt;&lt;Back</a></td>
</tr>
<tr>
  <td>
    <br>
    <table width="60%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="3" class="groupTitle"><%= _("New Display Style")%></td>
    </tr>
    <% if len(availableStylesheets) == 0: %>
    <tr>
      <td colspan="3"><%= _("All XSL stylesheets are already in use in a declared style. In order to add a new style, start by adding the corresponding .xsl file in")%> <%= styleMgr.getBaseXSLPath()%></td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Name")%></span></td>
      <td align="left" width="80%%"><input type="text" name="name" size="25"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("XSL Stylesheet")%></span></td>
      <td align="left">
        <select name="xslfile">
        <% for style in availableStylesheets: %>
          <option value="<%= style %>"><%= style %>.xsl</option>
        <% end %>
        </select>
        <% inlineContextHelp(contextHelpText) %>
      </td>
    </tr>
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" name="new" value="ok"></td>
    </tr>
    <% end %>
    </table>
  </td>
</tr>
</table>
</form>
