<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<div id="buttonBar" class="contributionButtonBar">
    % if Contribution.canModify(accessWrapper):
    <a href="${str(urlHandlers.UHContributionModification.getURL(Contribution))}" style="font-weight: bold" >${_("Edit")}</a> |
    % endif
    <a href="${str(urlHandlers.UHContribToPDF.getURL(Contribution))}" target="_blank">${_("PDF")}</a> |
    <a href="${str(urlHandlers.UHContribToXML.getURL(Contribution))}"" target="_blank">${_("XML")}</a>
    % if Contribution.isScheduled():
    |
    <a id="exportIcal${Contribution.getUniqueId()}" class="fakeLink exportIcal" data-id="${Contribution.getUniqueId()}">${_("iCal")}</a>
    % endif
    <%include file="ContributionICalExport.tpl" args="item=Contribution"/>
</div>

<h1 class="contributionTitle">
    ${Contribution.getTitle()}
    ${ "--" + _("WITHDRAWN") + "--" if isWithdrawn else "" }
</h1>
<div>
    <div class="contributionMainContent">
        <div class="contributionInformation">
            <%block name="speakers">
            </%block>
            <div class="contributionHeader">
                % if Contribution.getType() != None:
                    <div><span style="font-weight:bold">${_("Type")}: </span>${Contribution.getType().getName()}</div>
                % endif
                % if Contribution.getSession() is not None:
                    <div>
                        <span style="font-weight:bold">${_("Session")}: </span>
                        <a class="lightGreyLink" href="${str(urlHandlers.UHSessionDisplay.getURL(Contribution.getSession()))}">${Contribution.getSession().getTitle()}</a>
                        <div style="background-color: ${Contribution.getSession().getColor()};" class="sessionSquare"></div>
                    </div>
                % endif
                % if Contribution.getTrack() != None:
                    <div><span style="font-weight:bold">${_("Track")}: </span>${Contribution.getTrack().getTitle()}</div>
                % endif
                <%block name="board">
                </%block>
                <%block name="reportNumber">
                </%block>
            </div>
        </div>
        <div class="contributionDetail">
            <%block name="detail">
            </%block>
            % if Contribution.getSubContributionList():
            <div class="contributionSection">
                <h2 class="contributionSectionTitle">Subcontributions</h2>
                <div class="subContributionListSection">
                <ul>
                % for subcontrib in Contribution.getSubContributionList():
                    <li>
                    % if subcontrib.canModify(accessWrapper):
                        <a href="${str(urlHandlers.UHSubContributionModification.getURL(subcontrib))}">
                            <img  style="vertical-align: middle" src="${Config.getInstance().getSystemIconURL('edit')}" alt='${_("Modify subcontribution")}'>
                        </a>
                    % endif
                    <a href="${str(urlHandlers.UHSubContributionDisplay.getURL(subcontrib))}">${subcontrib.getTitle()}</a>
                    </li>
                % endfor
                </ul>
                </div>
            </div>
            % endif
        </div>
    </div>
    <div class="contributionRightPanel">
        <%block name="paperReview">
        </%block>
        <%block name="place">
        </%block>
        <%block name="authors">
        </%block>
        % if showAttachedFiles and abstractAttachments:
            <div class="contributionRightPanelSection">
                <h2 class="contributionSectionTitle">${_("Abstract files")}</h2>
                <ul>
                % for file in abstractAttachments:
                    <li><a href="${file['url']}" target="_blank">${file["file"]["fileName"]}</a>
                % endfor
                </ul>
            </div>
        % endif
            <% canEditFiles = (Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw)) and not isWithdrawn %>
            % if Contribution.getAllMaterialList() or canEditFiles:
            <div class="contributionRightPanelSection">
                <h2 class="contributionSectionTitle">${_("Files")}</h2>
                % if canEditFiles:
                <div style="float:right; line-height: 17px">
                    <a class="fakeLink" id="manageMaterial">Edit files</a>
                </div>
                % endif
                <ul>
                % for material in Contribution.getAllMaterialList():
                    <% if not material.canView(self_._aw):
                           continue
                     %>

                    <li><a href="${urlHandlers.UHMaterialDisplay.getURL(material)}" class="titleWithLink" title="${material.getDescription()}">
                        ${material.getTitle()}
                        </a>
                     <ul class="subList">
                     % for resource in material.getResourceList():
                     <li><a href="${urlHandlers.UHFileAccess.getURL(resource)}" target="_blank" title="${resource.getDescription()}">
                            ${getResourceName(resource)}
                        </a>
                        </li>
                     % endfor
                     </ul>
                     </li>
                % endfor
                </ul>
            </div>
            % endif
    </div>
</div>
<script type="text/javascript">
    $("#manageMaterial").click(function(){
        IndicoUI.Dialogs.Material.editor('${Contribution.getConference().getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}','${Contribution.getId()}','',
                ${jsonEncode(Contribution.getAccessController().isProtected())}, ${jsonEncode(Contribution.getMaterialRegistry().getMaterialList(Contribution.getConference()))}, ${'Indico.Urls.UploadAction.contribution'}, true);
     });
</script>
<%block name="scripts">

</%block>
