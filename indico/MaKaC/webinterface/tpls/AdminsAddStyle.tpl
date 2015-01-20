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
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Name")}</span></td>
      <td align="left" width="80%"><input type="text" name="name" size="25"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("ID")}</span></td>
      <td align="left" width="80%"><input type="text" name="styleID" size="25">
      ${inlineContextHelp(_("Style ID is used in URLs. It must be unique for every style."))}
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Template type")}</span></td>
      <td align="left">
          <input type="radio" value="tpl" name="templatetype" onclick="enableTypeTemplate('tpl');">TPL
          <input type="radio" value="xsl" name="templatetype" onclick="enableTypeTemplate('xsl');">XSL
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Template file")}</span></td>
      <td align="left">
        <select id="tplfile" name="tplfile" disabled>
        % for style in availableTemplates:
          <option value="${ style }">${ style }</option>
        % endfor
        </select>
        ${inlineContextHelp(tplContextHelpText)}
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Stylesheet file")}</span></td>
      <td align="left">
        <select id="stylesheetfile" name="stylesheetfile" disabled>
        % for style in availableStyleSheets:
          <option value="${ style }">${ style }</option>
        % endfor
        </select>
        ${inlineContextHelp(xslContextHelpText)}
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"></td>
      <td align="left">
            <input type="checkbox" id="cssCheckbox" name="useCss" value="use" checked="checked"/> Use CSS file for this style
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("CSS file")}</span></td>
      <td align="left">
        <select id="cssFileList" name="cssfile">
        % for css in availableCSS:
          <option value="${ css }">${ css }</option>
        % endfor
        </select>
        ${inlineContextHelp(cssContextHelpText)}
      </td>
    </tr>
    <tr>
      <td colspan="2" align="center"><input type="submit" class="btn" id="new" name="new" value="ok" disabled></td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
<script type="text/javascript">

    function enableTypeTemplate (type) {
        $('#stylesheetfile').prop('disabled', type != 'xsl');
        $('#tplfile').prop('disabled', type == 'xsl');
        $('#new').prop('disabled', false);
    }

    var cssFileList = $('#cssFileList');
    $('#cssCheckbox').on('change', function() {
        cssFileList.prop('disabled', !this.checked);
    });
</script>