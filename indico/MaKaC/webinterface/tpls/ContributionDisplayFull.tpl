<%inherit file="ContributionDisplayMin.tpl"/>

<%block name="speakers">
    <div class="contributionSpeakerList">
        <% speakers = [] %>
        % for speaker in Contribution.getSpeakerList():
            <% speakers.append(speaker.getDirectFullName()) %>
        % endfor
        % if speakers:
            ${_("Presented by")} <span style="font-weight: bold">${", ".join(speakers)} </span>
        % endif
        % if Contribution.isScheduled():
            ${_("on")}
            <span style="font-weight: bold">${formatDate(Contribution.getStartDate())}</span>
            ${_("from")}
            <span style="font-weight: bold">${formatTime(Contribution.getStartDate())}</span>
            ${_("to")}
            <span style="font-weight: bold">${formatTime(Contribution.getEndDate())}</span>
        % endif
    </div>
</%block>

<%block name="board">
    % if Contribution.getBoardNumber()!= "":
        <div><span style="font-weight:bold">${_("Board")} #: </span>${Contribution.getBoardNumber()}</div>
    % endif
</%block>

<%block name="detail">
    % if not self_._rh._target.getConference().getAbstractMgr().isActive() or not self_._rh._target.getConference().hasEnabledSection("cfa") or not self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
    <div class="contributionSection">
        <h2 class="contributionSectionTitle">Description</h2>
        <div class="contributionSectionContent">${Contribution.getDescription()}</div>
    </div>
    % else:
        % for f in Contribution.getConference().getAbstractMgr().getAbstractFieldsMgr().getActiveFields():
            % if Contribution.getField(f.getId()):
            <div class="contributionSection">
                <h2 class="contributionSectionTitle">${f.getName()}</h2>
                <div class="contributionSectionContent">${Contribution.getField(f.getId())}
                </div>
            </div>
            % endif
        % endfor
    % endif
</%block>

<%block name="paperReview">
    % if reviewingActive:
    <div class="contributionReviewingSection">
        <h2 class="contributionSectionTitle">${_("Call for papers")}</h2>
            <div>
                <div class="contributionReviewingStatus ${statusClass}">${statusText}</div>
                % if showSubmit:
                    <span class="fakeLink" id="revSubmit">${prefixUpload}Upload paper</span><br/>
                % endif
                <div style="white-space: nowrap">
                % if showHistory and len(Contribution.getReviewManager().getVersioning()) > 1:
                    <span class="fakeLink" id="revHistory">${_("History")}</span>
                % endif
                % if showHistory and len(Contribution.getReviewManager().getVersioning()) > 1 and showMaterial:
                 |
                % endif
                % if showMaterial:
                    <span class="fakeLink" id="revMaterial">${_("View Paper")}</span>
                % endif
                </div>
            </div>
        </div>
    % endif
</%block>

<%block name="place">
    <% import MaKaC.webinterface.linking as linking %>
    <% location = Contribution.getLocation() %>
    <% room = Contribution.getRoom() %>
    % if location or room:
    <div class="contributionRightPanelSection">
        <h2 class="contributionSectionTitle">${_("Place")}</h2>
        <div>
        % if location:
            <div><span style="font-weight:bold">${_("Location")}: </span>${location.getName()}</div>
            % if location.getAddress() is not None and location.getAddress()!="":
            <div><span style="font-weight:bold">${_("Address")}: </span>${location.getAddress()}</div>
            % endif
        % endif
        % if room:
            <div><span style="font-weight:bold">${_("Room")}: </span>${linking.RoomLinker().getHTMLLink(room,location)}</div>
        % endif
        </div>
    </div>
    % endif
</%block>

<%block name="authors">
    % if Contribution.getPrimaryAuthorList():
        <div class="contributionRightPanelSection">
            <h2 class="contributionSectionTitle">${_("Primary authors")}</h2>
            <ul>
            % for pa in Contribution.getPrimaryAuthorList()[:4]:
                <li><a href="${getAuthorURL(pa)}">${pa.getDirectFullNameNoTitle()}</a>
                    <span style="font-size:10px">${pa.getAffiliation()}</span>
            % endfor
            </ul>
            <a class="fakeLink" id="moreAuthors">${_("More")}</a>
        </div>
    % endif
    % if Contribution.getCoAuthorList():
        <div class="contributionRightPanelSection">
            <h2 class="contributionSectionTitle">${_("Co-authors")}</h2>
            <ul>
            % for ca in Contribution.getCoAuthorList()[:4]:
                <li><a href="${getAuthorURL(ca)}">${ca.getDirectFullNameNoTitle()}</a>
                    <span style="font-size:10px">${ca.getAffiliation()}</span>
            % endfor
            </ul>
            <a class="fakeLink" id="moreCoAuthors">${_("More")}</a>
        </div>
    % endif
</%block>

<%block name="scripts">
<script type="text/javascript">
    var args = {
        conference: '${ Contribution.getConference().getId() }',
        confId: '${ Contribution.getConference().getId() }',
        contribution: '${ Contribution.getId() }',
        contribId: '${ Contribution.getId() }',
        parentProtected: ${ jsBoolean(Contribution.getAccessController().isProtected()) }
    };
    $("#moreAuthors").click(function(){
        var popupAuthors = new AuthorsPopup($T("Primary authors"), ${fossilize(Contribution.getPrimaryAuthorList())}, '${Contribution.getConference().getId()}', '${Contribution.getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}', function() {self.popupAllowClose = true; return true;});
        popupAuthors.open();
    });

    $("#moreCoAuthors").click(function(){
        var popupCoAuthors = new AuthorsPopup($T("Co authors"), ${fossilize(Contribution.getCoAuthorList())}, '${Contribution.getConference().getId()}', '${Contribution.getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}', function() {self.popupAllowClose = true; return true;});
        popupCoAuthors.open();
    });

    $("#revSubmit").click(function(){
        var popupSubmit = new SubmitPopup($T("Paper selection and submission"), args, '${urlHandlers.UHContributionSubmitForRewiewing.getURL(Contribution)}');
        popupSubmit.open();
    });

    $("#revMaterial").click(function(){
        var killProgress = IndicoUI.Dialogs.Util.progress();
        jsonRpc(Indico.Urls.JsonRpcService, "material.reviewing.list", args,
                function(result, error){
                    killProgress();
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                    } else {
                        var popupMaterial = new UploadedPaperPopup($T("Submitted paper"), result.reviewing.resources);
                        popupMaterial.open();
                    }
        });
    });

    $("#revHistory").click(function(){
        var killProgress = IndicoUI.Dialogs.Util.progress();
            jsonRpc(Indico.Urls.JsonRpcService, "contribution.review.getReviewHistory",
                    {confId: '${Contribution.getConference().getId()}',
                     contribId: '${Contribution.getId()}'},
                    function(result, error){
                        killProgress();
                        if (exists(error)) {
                            IndicoUtil.errorReport(error);
                        } else {
                            var popup = new ExclusivePopup($T('Review History'), null, true, true);
                            popup.draw = function() {
                                this.ExclusivePopup.prototype.draw.call(this, result, {minWidth: pixels(400), maxWidth:pixels(800), maxHeight:pixels(800)});
                            };
                            popup.open();
                        }
            });
        });

</script>
</%block>
