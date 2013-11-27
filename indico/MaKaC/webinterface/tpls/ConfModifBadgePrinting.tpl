<h2>${ _("Create a New Template")}</h2>

<div>
  ${ _("Based on")}:
<form action='${ NewTemplateURL }' method='post' style="display:inline;">
  <select name="baseTemplate">
  % for template in baseTemplates:
    <option value="${template['value']}">
      ${template['label']}
    </option>
  % endfor
  </select>
  <input class="i-button" name="New Template Button" value="${ _('Create New Template')}" type="submit"/>
</form>
</div>

% if templateList:
  <form action='${CreatePDFURL}' method='post' target='_blank' id="create_form">
    <div id="config_data" style="display:none"></div>
    <h2 style="margin-top: 2em;">${ _("Available Templates")}</h2>

    ${_("Select the required template below then you may click the download button to obtain the generated PDF.")}

    <div class="template_list">
      <ul>
        % for template in templateList:
          <li>
            <input type="radio" name="templateId" value="${template['id']}" />
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

      <a href="#" id="showPDFLayout" class="i-button icon-settings right">${_("Layout Settings")}</a>

      <%block name="download_button">
        <button class="i-button" id="downloadPDF" style="margin-left: 3em;">
          <i class="icon-file-download" aria-hidden="true"></i>
          ${('Download Badges PDF')}
        </button>
      </%block>
    </div>
  </form>

<div id="badgePDFOptions" title="PDF Options">
  ${PDFOptions}
</div>

% endif


