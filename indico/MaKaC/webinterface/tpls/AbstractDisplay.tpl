<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>
<% from MaKaC.review import AbstractStatusWithdrawn %>


<div class="contribution-display">
    <div class="layout-wrapper">
        <div id="buttonBar" class="toolbar right">
            <div class="group">
                % if abstract.canModify(accessWrapper):
                    % if not modifyDisabled:
                        <a href="${modifyURL}" class="i-button icon-edit" title="${_("Edit")}"></a>
                    % endif
                    % if isinstance(abstract.getCurrentStatus(), AbstractStatusWithdrawn):
                        <a href="${recoverURL}" class="i-button" title="${_("Recover")}">${_("Recover")}</a>
                    % elif not withdrawDisabled:
                        <a href="${withdrawURL}" class="i-button icon-remove" title="${_("Withdraw")}"></a>
                    % endif
                % endif
                <a href="${str(urlHandlers.UHAbstractDisplayPDF.getURL(abstract))}" 
                   class="i-button icon-file-pdf" target="_blank" title="${_("Generate PDF")}"></a>
            </div>
        </div>
        <h1 class="page_title">${"Abstract"}</h1>
    </div>
    <div class="layout-wrapper clear">
        <div class="aside" title="${_("Submission details (date, time and user)")}">
            <time datetime="${abstract.getSubmissionDate().isoformat()}">
                ${formatDateTime(abstract.getSubmissionDate())}
            </time>
            <div class="user icon-user">
                ${abstract.getSubmitter().getStraightFullName()}
            </div>
        </div>
        <h1>
            ${abstract.getTitle()}
        </h1>
    </div>
    <div class="clear">
        <div>
            <div class="information">
                <div class="status ${statusClass}" title="${_("Abstract status")}">${statusText}</div>
                <div class="layout-wrapper">
                    % if abstract.getPrimaryAuthorList():
                        <div class="column">
                            <h2>${_("Primary authors")}</h2>
                            <ul>
                            % for pa in abstract.getPrimaryAuthorList():
                                <li class="icon-user">
                                  ${pa.getStraightFullName()} (${pa.getAffiliation()})
                                </li>
                            % endfor
                            </ul>
                        </div>
                    % endif
                    % if abstract.getCoAuthorList():
                        <div class="column">
                            <h2>${_("Co-authors")}</h2>
                            <ul>
                            % for ca in abstract.getCoAuthorList():
                                <li class="icon-user">
                                  ${ca.getStraightFullName()} (${ca.getAffiliation()})
                                </li>
                            % endfor
                            </ul>
                        </div>
                    % endif
                    % if abstract.getSpeakerList():
                        <div class="column">
                            <h2>${_("Presenters")}</h2>
                            <ul>
                            % for sp in abstract.getSpeakerList():
                                <li class="icon-user">
                                  ${sp.getStraightFullName()} (${sp.getAffiliation()})
                                </li>
                            % endfor
                            </ul>
                        </div>
                    % endif
                    % if len(attachments) != 0:
                        <div class="column files">
                            <h2>${_("Attached files")}</h2>
                            <ul>
                                % for file in attachments:
                                    <li class="icon-file"><a href="${file['url']}">${ file["file"]["fileName"] }</a></li>
                                % endfor
                            </ul>
                        </div>
                    % endif
                </div>
                <ul class="extra-parameters clear">
                    <li>
                        <span class="name">${_("Abstract ID")}:</span>
                        <span class="value">${abstract.getId()}</span>
                    </li>
                    <li>
                        <span class="name">${_("Last modification time")}:</span>
                        <span class="value">${formatDateTime(abstract.getModificationDate())}</span>
                    <li>
                    % if contribType:
                        <li>
                            <span class="name">${_("Contribution type")}:</span>
                            <span class="value">${contribType.getName()}</span>
                        <li>
                    % endif
                    % if False:
                        <li>
                            <span class="name">${_("Track classification")}:</span>
                            <span class="value">${",".join([t.getTitle() for t in tracks])}</span>
                        <li>
                    % endif
                </ul>
                <div class="trigger icon-expand" data-hidden="true"></div>
            </div>
        </div>
        <div class="main-content">
            <div class="contributionDetail">
                % for f in abstract.getConference().getAbstractMgr().getAbstractFieldsMgr().getActiveFields():
                        % if abstract.getField(f.getId()):
                          <% content = str(abstract.getField(f.getId()))%>
                          <div class="section">
                            <h2>${f.getCaption()}</h2>
                            <div class="content md-preview-wrapper display">${content | m}</div>
                        </div>
                        % endif
                % endfor
                % if abstract.getComments():
                    <div class="section">
                        <h2>${_("Comments")}</h2>
                        <div class="content">${abstract.getComments()}</div>
                    </div>
                % endif
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
% if statusComments:
    $(".abstractStatus").qtip({
        content: " ${statusComments}",
        position :{
            at: "bottom middle",
            my: "top middle"
        }
    });
% endif

</script>
