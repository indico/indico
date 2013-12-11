<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<div class="contribution-display">
    <div class="layout-wrapper">
        <div id="buttonBar" class="toolbar right">
            <div class="group">
                % if Contribution.canModify(accessWrapper):
                        <a href="${str(urlHandlers.UHContributionModification.getURL(Contribution))}" class="i-button icon-edit" title="${_("Edit")}"></a>
                % endif
                <a href="${str(urlHandlers.UHContribToPDF.getURL(Contribution))}"
                   class="i-button icon-file-pdf" target="_blank" title="${_("Generate PDF")}"></a>
                <a href="${str(urlHandlers.UHContribToXML.getURL(Contribution))}"
                   class="i-button icon-file-xml" target="_blank" title="${_("Generate XML")}"></a>
                % if Contribution.isScheduled():
                    <a id="exportIcal${Contribution.getUniqueId()}" class="i-button icon-calendar exportIcal" data-id="${Contribution.getUniqueId()}"></a>
                    <%include file="ContributionICalExport.tpl" args="item=Contribution"/>
                % endif
            </div>
        </div>
        <h1 class="page_title">${"Contribution"} ${"({0})".format(_("WITHDRAWN")) if isWithdrawn else "" }</h1>
    </div>

    <div class="layout-wrapper clear">
        <div class="aside left-align">
            % if Contribution.isScheduled():
                <time datetime="${Contribution.getStartDate().isoformat()}" class="icon-time">
                    ${formatDateTime(Contribution.getStartDate())}
                    - ${formatTime(Contribution.getEndDate())}
                </time>
                <%block name="place">
                </%block>
            % endif
        </div>
        <h1>
            ${Contribution.getTitle()}
        </h1>
    </div>

     <div class="clear">
            <div>
                <div>
                    % if Contribution.getTrack():
                        <div class="track-assignment">${Contribution.getTrack().getTitle()}</div>
                    % endif

                    % if Contribution.getSession():
                        <div class="session-assignement">
                          <a class="lightGreyLink" href="${str(urlHandlers.UHSessionDisplay.getURL(Contribution.getSession()))}">
                            ${Contribution.getSession().getTitle()}
                          </a>
                          <div style="background-color: ${Contribution.getSession().getColor()};" class="sessionSquare"></div>
                        </div>
                    % endif
                </div>
                <div class="information">
                    <div class="layout-wrapper">
                        <%block name="paperReview">
                        </%block>

                        <%block name="speakers">
                        </%block>

                        <%block name="authors">
                        </%block>

                        <%block name="coauthors">
                        </%block>

                        <div class="row files">

                            % if showAttachedFiles and abstractAttachments:
                            <div class="column">
                                <h2>${_("Abstract files")}</h2>
                                <ul>
                                % for file in abstractAttachments:
                                    <li class="icon-file"><a href="${file['url']}" target="_blank">${file["file"]["fileName"]}</a></li>
                                % endfor
                                </ul>
                            </div>
                            % endif


                            <% materialList = Contribution.getAllViewableMaterialList() %>
                            <% canEditFiles = (Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw)) and not isWithdrawn %>

                            % if materialList or canEditFiles:
                                <div class="column ${'highlighted-area' if canEditFiles else ''}">
                                    % if canEditFiles:
                                        <div class="right">
                                            <a href="#" id="manageMaterial" class="i-button icon-edit"></a>
                                        </div>
                                    % endif
                                    <h2>${_("Files")}</h2>
                                    <ul>
                                    % for material in materialList:

                                        <li>
                                            <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}" class="titleWithLink" title="${material.getDescription()}">
                                                <h3>${material.getTitle()}</h3>
                                            </a>
                                            <ul>
                                            % for resource in material.getResourceList():
                                                <li class="icon-file">
                                                    <a href="${urlHandlers.UHFileAccess.getURL(resource)}" target="_blank" title="${resource.getDescription()}">
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
                        <ul class="extra-parameters clear">
                            % if Contribution.getType() != None:
                                <li>
                                    <span class="name">${_("Contribution type")}:</span>
                                    <span class="value">${Contribution.getType().getName()}</span>
                                </li>
                            % endif
                            <%block name="board">
                            </%block>
                            <%block name="reportNumber">
                            </%block>
                        </ul>
                        <div class="trigger icon-expand" data-hidden="true"></div>
                    </div>
                </div>
            </div>

    <div>
        <div class="contribution-display">
            <%block name="detail">
            </%block>
            % if Contribution.getSubContributionList():
            <div class="section">
                <h2>Subcontributions</h2>
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
<script type="text/javascript">
    $("#manageMaterial").click(function(){
        IndicoUI.Dialogs.Material.editor('${Contribution.getConference().getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}','${Contribution.getId()}','',
                ${jsonEncode(Contribution.getAccessController().isProtected())}, ${jsonEncode(Contribution.getMaterialRegistry().getMaterialList(Contribution.getConference()))}, ${'Indico.Urls.UploadAction.contribution'}, true);
     });
</script>
<%block name="scripts">

</%block>
