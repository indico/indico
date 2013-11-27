<h2>
  ${ _("Default Poster Templates")}
</h2>

<div>
  ${_("Click 'Create New Template' to make a new global Poster template for any Indico users to make use of, or you can edit previously saved templates below.")}
</div>


% if templateList:

<div class="template_list">
  <ul>
    % for template in templateList:
    <li>
        <span class="name">${template['name']}</span>
        <div class="toolbar right thin inline">
          <div class="group">
            <a href="${template['urlEdit']}" class="i-button icon-edit icon-only" title="${_("Edit template")}"></a>
            <a href="${template['urlCopy']}" class="i-button icon-copy icon-only" title="${_("Clone template")}"></a>
            <a href="${template['urlDelete']}" class="i-button icon-remove icon-only" title="${_("Delete template")}"></a>
          </div>
        </div>
    </li>
    % endfor
  </ul>
</div>
% else:
    ${_('There are currently no templates saved.')}
% endif
<div>
  <a class="i-button icon-plus" href="${ NewDefaultTemplateURL }" style="margin-top: 1em;">${_('Create New Template')}</a>
</div>