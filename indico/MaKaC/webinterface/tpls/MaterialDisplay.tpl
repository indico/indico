<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import Link %>
<% from MaKaC.webinterface.general import strfFileSize %>
<div id="buttonBar" class="materialButtonBar">
% if (material.canModify(accessWrapper) or canSubmitResource):
    <span id="manageMaterial" class="fakeLink" style="font-weight: bold">${_("Edit")}</span>
% endif
</div>

<h1 class="materialTitle">
    ${material.getTitle()}
    <div class="materialDescription">${material.getDescription()}</div>
</h2>
<div>
    <div class="materialMainContent">
        <div class="materialDetail">
            % if material.getResourceList() and material.canView(accessWrapper):
            <div class="materialSection">
                <div>
                <ul>
                % for resource in material.getResourceList():
                    <li>
                    % if isinstance(resource, Link):
                        <img src="${Config.getInstance().getSystemIconURL('link')}" style="vertical-align: middle; border: 0;">
                        <a href="${getURL(resource)}">${resource.getName() if resource.getName() != "" and resource.getName() != resource.getURL() else resource.getURL()}</a>
                        % if resource.getDescription().strip():
                        <ul class="resourceDetail">
                            <li>${resource.getDescription()}</li>
                        </ul>
                        % endif
                        % if resource.isProtected():
                            <img src="${Config.getInstance().getSystemIconURL('protected')}" style="vertical-align: middle; border: 0;">
                        % endif
                    % else:
                        <% image = Config.getInstance().getFileTypeIconURL( resource.getFileType()) %>
                        <img src="${image if image else Config.getInstance().getSystemIconURL('smallfile')}" style="vertical-align: middle; border: 0;">
                        <a href="${fileAccessURLGen(resource)}">${resource.getName()}</a>
                        % if resource.isProtected():
                            <img src="${Config.getInstance().getSystemIconURL('protected')}" style="vertical-align: middle; border: 0;">
                        % endif
                        <ul class="resourceDetail">
                            <li>${resource.getDescription()}</li>
                            <li><span style="font-weight: bold">${_("File name")}: </span>${resource.getFileName()}</li>
                            <li><span style="font-weight: bold">${_("File size")}: </span>${strfFileSize(resource.getSize())}</li>
                            <li><span style="font-weight: bold">${_("File creation date")}: </span>${resource.getCreationDate().strftime("%d %b %Y %H:%M")}</li>
                        </ul>
                    % endif
                    </li>
                % endfor
                </ul>
                </div>
            </div>
            % endif
        </div>
    </div>
</div>

<script type="text/javascript">
    $("#manageMaterial").click(function(){
        IndicoUI.Dialogs.Material.editor('${material.getConference().getOwner().getId() if material.getConference() else ""}',
            '${material.getConference().getId() if material.getConference() else ""}', '${material.getSession().getId() if material.getSession() else ""}',
                '${material.getContribution().getId() if material.getContribution() else ""}','${material.getSubContribution().getId() if material.getSubContribution() else ""}',
                ${jsonEncode(material.getOwner().getAccessController().isProtected())}, ${jsonEncode(material.getOwner().getMaterialRegistry().getMaterialList(material.getOwner()))}, ${uploadAction}, true);
     });
</script>
