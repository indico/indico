  <table class="gestiontable" style="text-align: left; width: 95%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td  colspan="2" class="groupTitle">
           ${ _("Generate a Poster")}
        </td>
      </tr>
      <tr>
        <td colspan="2">
            <div class="bs-alert bs-alert-info alert-toolbar">
              <span class="bs-btn bs-btn-info" id="showPDFLayout" style="float:right;">${_('PDF Layout Options')}</span>
            ${_("The page layout and dimensions will be the default for this event, if you would like to review and/or edit these, please click on the PDF Layout button.")}
            <div class="toolbar-clearer"></div>
           </div>
        </td>
      </tr>
      <form action='${ CreatePDFURL }' method='post' target='_blank'>
      <tr class="trBottomSpacer">
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
          <div style="display:none;">
            <div id="badgePDFOptions" title="PDF Options">
              ${ PDFOptions }
            </div>
          </div>
        </form>
        </td>
      </tr>
      <tr>
        <td colspan="2" class="groupTitle">
           ${ _("Create New Local Poster Template")}
        </td>
      </tr>
     <tr class="trBottomSpacer">
        <form action='${ NewTemplateURL }' method='post'>
        <td class="titleCellTD" NOWRAP>
          ${ _("Based on:")}
        </td>
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

      % if templateList:
      <tr>
        <td colspan="2" class="groupTitle">
           ${ _("Current Local Poster Templates")}
        </td>
      </tr>

      <tr>
        <td colspan="2">
          <table>
            <tbody>
              % for template in templateList:
              <tr>
                <td>
                  <a href="${template['urlEdit']}" class='bs-btn bs-btn-mini'>${_('Edit')}</a>
                  <a href="${template['urlCopy']}" class='bs-btn bs-btn-mini'>${_('Clone')}</a>
                  <a href="${template['urlDelete']}" class='bs-btn bs-btn-mini'>${_('Delete')}</a>
                </td>
                <td style="padding-left:5px;">
                  ${template['name']}
                </td>
              </tr>
              % endfor
            <tbody>
          </table>
        </td>
      </tr>
      % endif

    </tbody>
  </table>
