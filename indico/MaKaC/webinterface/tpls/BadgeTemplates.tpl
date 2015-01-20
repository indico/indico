<h2>
  ${_("Default Badge Templates")}
  ${inlineContextHelp(_('Templates that will be available for all conferences.'))}
</h2>

<div>
  ${_("Click 'Create New Template' to make a new global Badge template for any Indico users to make use of, or you can edit previously saved templates below")}
</div>

<div class="template_list">
  <ul>
    % if templateList:
      % for template in templateList:
        <li>
          <span class="name">${template['name']}</span>
          <div class="toolbar right thin inline">
            <div class="group">
              <a href="${template['urlEdit']}" class="i-button icon-edit icon-only" title="${_("Edit template")}"></a>
              <a href="${template['urlDelete']}" class="i-button icon-remove icon-only" title="${_("Delete template")}"></a>
            </div>
          </div>
        </li>
      % endfor
    % else:
        <li class="text-superfluous">${_('There are currently no templates saved.')}</li>
    % endif
  </ul>
</div>

<div>
  <a class="i-button icon-plus" href="${ NewDefaultTemplateURL }" style="margin-top: 1em;">${_('Create New Template')}</a>
</div>

<h3 class="clear">
  ${ _("Default PDF Options")}
  ${inlineContextHelp(_('Initial PDF options after a conference is created.') )}
</h3>

<form method="post" action="${urlHandlers.UHTemplatesSetDefaultPDFOptions.getURL()}">
  <div class="bs-alert bs-alert-info">
    <input name="savePDFOptions" class="i-button accept right" value="${ _("Save")}" type="submit">
    ${_('Once you have modified the default settings, please click save to put the amendments into effect.')}
  </div>
  ${PDFOptions}
