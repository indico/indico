<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<div class="contribution-display">
    <div class="layout-wrapper">
        <div id="buttonBar" class="toolbar right">
            % if Contribution.canModify(accessWrapper):
            <div class="group">
              <a href="${str(urlHandlers.UHContributionModification.getURL(Contribution))}" class="i-button icon-edit" title="${_("Edit")}"></a>
            </div>
            % endif
            <div class="group">
                <a href="${str(urlHandlers.UHContribToPDF.getURL(Contribution))}"
                   class="i-button icon-file-pdf" target="_blank" title="${_("Generate PDF")}"></a>
                <a href="${str(urlHandlers.UHContribToXML.getURL(Contribution))}"
                   class="i-button icon-file-xml" target="_blank" title="${_("Generate XML")}"></a>
                % if Contribution.isScheduled():
                    <a id="exportIcal${Contribution.getUniqueId()}" class="i-button icon-calendar exportIcal" data-id="${Contribution.getUniqueId()}"></a>
                % endif
            </div>
            <%include file="ContributionICalExport.tpl" args="item=Contribution"/>
        </div>
        <h1 class="page-title">
            ${_("Contribution")}
            % if Contribution.getType() is not None:
                <span class="type">${Contribution.getType().getName()}</span>
            % endif

            ${"({0})".format(_("WITHDRAWN")) if isWithdrawn else "" }
        </h1>
    </div>

    <div class="schedule-info layout-wrapper clear">
        <div class="aside">
            % if Contribution.isScheduled():
                <time datetime="${Contribution.getStartDate().isoformat()}">
                    ${formatDateTime(Contribution.getStartDate())}
                    - ${formatTime(Contribution.getEndDate())}
                </time>
                <%block name="place">
                </%block>
            % endif
        </div>
        <div class="clear aside assignments">
            % if Contribution.getTrack():
                <div class="track-assignment">${Contribution.getTrack().getTitle()}</div>
            % endif

            % if Contribution.getSession():
                <div class="session-assignment">
                  <div style="background-color: ${Contribution.getSession().getColor()};" class="square"></div>
                  <a href="${str(urlHandlers.UHSessionDisplay.getURL(Contribution.getSession()))}">
                    ${Contribution.getSession().getTitle()}
                  </a>
                </div>
            % endif
        </div>
        <h1>
            ${Contribution.getTitle()}
        </h1>
    </div>

     <div class="clear">
            <div>
                <div class="information">
                    <div class="layout-wrapper">
                        <%block name="speakers">
                        </%block>

                        <%block name="authors">
                        </%block>

                        <%block name="paperReview">
                        </%block>

                        <%block name="coauthors">
                        </%block>

                        <div class="row files extra-parameters">

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


                            <% canEditFiles = (Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw)) and not isWithdrawn %>

                            % if Contribution.attached_items or canEditFiles:
                                <div class="column">
                                    ${ render_template('attachments/mako_compat/attachments_tree.html', linked_object=Contribution, can_edit=canEditFiles) }
                                </div>
                                % endif
                            </div>
                            <div class="trigger icon-collapse" data-hidden="false"></div>
                        </div>
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
</div>
<script>
    setupAttachmentTreeView();
</script>
<%block name="scripts">

</%block>
