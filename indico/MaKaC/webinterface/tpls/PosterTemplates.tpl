
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td class="groupTitle">
           ${ _("Default Poster Templates")}
        </td>
      </tr>

      <tr>
        <td>
          <div class="bs-alert bs-alert-info alert-toolbar">
              <a class="btn btn-info btn-right" href="${ NewDefaultTemplateURL }">${_('Create New Template')}</a>
              ${_("Click 'Create New Template' to make a new global Poster template for any Indico users to make use of, or you can edit previously saved templates below.")}
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
                  <a href="${template['urlCopy']}" class='btn btn-mini'>${_('Clone')}</a>
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
      % else:
      <tr>
        <td>
          ${_('There are currently no templates saved.')}
        </td>
      </tr>
      % endif

    </tbody>
  </table>
