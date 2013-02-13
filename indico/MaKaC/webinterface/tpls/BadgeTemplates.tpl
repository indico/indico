
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td class="groupTitle">
          ${ _("Default Badge Templates")}
          ${inlineContextHelp(_('Templates that will be available for all conferences.') )}
        </td>
      </tr>

      <tr>
        <td>
          <div class="bs-alert bs-alert-info alert-toolbar">
              <a class="btn btn-right btn-info" href="${ NewDefaultTemplateURL }">${_('Create New Template')}</a>
              ${_("Click 'Create New Template' to make a new global Badge template for any Indico users to make use of, or you can edit previously saved templates below")}
            <div class="toolbar-clearer"></div>
           </div>
        </td>
      </tr>

      % if templateList:
      <tr class="trBottomSpacer">
        <td>
          <table>
            <tbody>
              % for template in templateList:
              <tr>
                <td>
                  <a href="${template['urlEdit']}" class='btn btn-mini'>${_('Edit')}</a>
                  <a href="${template['urlDelete']}" class='btn btn-mini'>${_('Delete')}</a>
                </td>
                <td style="padding-left:5px;">
                  ${template['name']}
                </td>
              </tr>
              % endfor
          </table>
        </td>
      </tr>

      <tr>
        <td class="groupTitle">
          ${ _("Default PDF Options")}
          ${inlineContextHelp(_('Initial PDF options after a conference is created.') )}
        </td>
      </tr>
<form method="post" action="${urlHandlers.UHTemplatesSetDefaultPDFOptions.getURL()}">
     <tr>
       <td>
        <div class="bs-alert bs-alert-info">
          <input name="savePDFOptions" class="btn btn-right" value="${ _("Save")}" type="submit">
        ${_('Once you have modified the default settings, please click save to put the amendments into effect.')}
        <div class="toolbar-clearer"></div>
       </div>
       </td>
     </tr>
    <tr>
      <td>
        ${PDFOptions}
        </form>
      </td>
    </tr>
    % else:
      <tr>
        <td>
          ${_('There are currently no templates saved.')}
        </td>
      </tr>
    % endif

    </tbody>
  </table>
