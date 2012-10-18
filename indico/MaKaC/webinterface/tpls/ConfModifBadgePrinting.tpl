  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td  colspan="2" class="groupTitle">
            ${ _("Create a New Template")}
        </td>
      </tr>
      <tr>
          <td class="titleCellTD">
             ${ _("Based on")}:
          </td>
          <td>
            <form action='${ NewTemplateURL }' method='post'>
            <select name="baseTemplate">
              % for template in baseTemplates:
                <option value="${template['value']}">
                  ${template['label']}
                </option>
              % endfor
            </select>
            <input name="New Template Button" value="${ _('Create New Template')}" type="submit">
            </form>
          </td>
      </tr>
    </tbody>
  </table>
  % if templateList:
  <form action='${CreatePDFURL}' method='post' target='_blank'>
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="2" class="groupTitle">
            ${ _("Available Templates")}
        </td>
      </tr>
      <tr>
        <td colspan="2">
          <table class="gestiontable">
            <thead>
              <tr>
                <td colspan=3>
                  <div class="bs-alert bs-alert-info">
                    <input type="submit" value="${('Download Badges PDF')}" class="bs-btn" style="float:right;" id="downloadPDF" />
                  ${_("Select the required template below then you may click the download button to obtain the generated PDF.")}
                  <div class="toolbar-clearer"></div>
                 </div>
                </td>
              </tr>
            </thead>
            <tbody>
              % for template in templateList:
              <tr>
                <td width='5%'>
                  <input type="radio" name="templateId" value="${template['id']}" />
                </td>
                <td>
                  ${template['name']}
                </td>
                <td align='right'>
                  <a href="${template['urlEdit']}" class='bs-btn bs-btn-mini'>Edit</a>
                  <a href="${template['urlCopy']}" class='bs-btn bs-btn-mini'>Clone</a>
                  <a href="${template['urlDelete']}" class='bs-btn bs-btn-mini'>Delete</a>
                </td>
              </tr>
              % endfor
              <tr>
                <td colspan=3>
                  &nbsp;
                </td>
              </tr>
              <tr>
                <td colspan=3>
                  <div class="bs-alert bs-alert-info alert-toolbar">
                    <span class="bs-btn bs-btn-info" id="showPDFLayout" style="float:right;">PDF Layout Options</span>
                  ${_("The page layout and dimensions will be the default for this event, if you would like to review and/or edit these, please click on the PDF Layout button.")}
                  <div class="toolbar-clearer"></div>
                 </div>
                </td>
              </tr>
          </table>
        </td>
      </tr>
    </tbody>
  </table>
  <div >
    <div id="badgePDFOptions" title="PDF Options">
      ${PDFOptions}
    </div>
  </div>
  </form>

  % endif
