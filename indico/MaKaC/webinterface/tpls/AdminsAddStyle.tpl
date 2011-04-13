<form action="${urlHandlers.UHAdminsStyles.getURL()}" method="POST">
<table align="center" width="95%">
<tr>
  <td class="formTitle"><a href="${urlHandlers.UHAdminsStyles.getURL()}">&lt;&lt;Back</a></td>
</tr>
<tr>
  <td>
    <br>
    <table width="60%" border="0">
    <tr>
      <td colspan="3" class="groupTitle">${ _("New Display Style")}</td>
    </tr>
    % if len(availableStyles) == 0:
    <tr>
      <td colspan="3">${ _("All template files are already in use in a declared style. In order to add a new style, start by adding the corresponding .tpl file in") } ${ styleMgr.getBaseTPLPath()}</td>
    </tr>
    % else:
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Name")}</span></td>
      <td align="left" width="80%"><input type="text" name="name" size="25"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("ID")}</span></td>
      <td align="left" width="80%"><input type="text" name="styleID" size="25">
      ${inlineContextHelp(_("Style ID is used in URLs and for naming the CSS file. It must be unique for every style."))}
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Template file")}</span></td>
      <td align="left">
        <select name="tplfile">
        % for style in availableStyles:
          <option value="${ style }">${ style }</option>
        % endfor
        </select>
        ${inlineContextHelp(contextHelpText)}
      </td>
    </tr>
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" name="new" value="ok"></td>
    </tr>
    % endif
    </table>
  </td>
</tr>
</table>
</form>
