  <table class="gestiontable" style="text-align: left; width: 95%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td  colspan="2" class="groupTitle">
           ${ _("Create a New Poster Template")}
        </td>
      </tr>
      <form action='${ CreatePDFURL }' method='post' target='_blank'>
      <tr>
          <td class="titleCellTD" NOWRAP>
            ${ _("Based on:")}
          </td>
        <td>
          <select name="templateId">
          % for template in fullTemplateList:
            <option value="${template['value']}">${template['label']}</option>
          % endfor
          </select>
          <input class="btn" value="${ _("Create Poster From Template")}" type="submit">
        </td>
      </tr>

      %if templateList:
      <tr>
        <td colspan="2" class="groupTitle">
           ${ _("Available Poster Templates")}
        </td>
      </tr>

      <tr>
        <td colspan="2">
          <form action='${ NewTemplateURL }' method='post'>
          <table>
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
            <tbody>
          </table>
        </td>
      </tr>
     <tr>
         <td></td>
        <td>
          <select name="baseTemplate">
          % for template in baseTemplateList:
            <option value="${template['value']}">${template['label']}</option>
          % endfor
          </select>
          <input name="New Template Button" class="btn" value="${ _("New")}" type="submit">
          </form>
        </td>
     </tr>
     % endif

    </tbody>
  </table>

% if templateList:
<div style="visibility:hidden;">
  <div id="badgePDFOptions" title="PDF Options">
    ${ PDFOptions }
  </div>
</div>
% endif
