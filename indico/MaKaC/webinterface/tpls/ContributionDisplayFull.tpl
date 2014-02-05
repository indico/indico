<%inherit file="ContributionDisplayMin.tpl"/>

<%block name="speakers">
    <div class="column">
        <h2>${_("Speakers")}</h2>
        <ul>
        % for speaker in Contribution.getSpeakerList():
            <li class="icon-user">${speaker.getDirectFullName()}</li>
        % endfor
        </ul>
    </div>
</%block>

<%block name="board">
    % if Contribution.getBoardNumber()!= "":
        <div><span style="font-weight:bold">${_("Board")} #: </span>${Contribution.getBoardNumber()}</div>
    % endif
</%block>

<%block name="reportNumber">
    % if Contribution.getReportNumberHolder().listReportNumbers():
        <div><span style="font-weight:bold">${_("Report Numbers")}:</span>
        % for reportNumber in Contribution.getReportNumberHolder().listReportNumbers():
            % if reportNumberSystems[reportNumber[0]]["url"]:
                <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
            % else:
                ${reportNumber[1]}
            % endif
        % endfor
        </div>
    % endif
</%block>

<%block name="detail">
    % if not Contribution.getConference().getAbstractMgr().isActive() or not Contribution.getConference().hasEnabledSection("cfa") or not Contribution.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
        % if Contribution.getDescription().strip()!="":
        <div class="section">
            <h2>Description</h2>
            <div class="content">${Contribution.getDescription()}</div>
        </div>
        % endif
    % else:
        % for f in Contribution.getConference().getAbstractMgr().getAbstractFieldsMgr().getActiveFields():
            % if Contribution.getField(f.getId()):
            <% content = Contribution.getField(f.getId()) %>
            <div class="section">
                <h2>${f.getCaption()}</h2>
                <div class="content md-preview-wrapper display">${content | m}</div>
            </div>
            % endif
        % endfor
    % endif
</%block>

<%block name="paperReview">
    % if reviewingActive:
    <div class="column reviewing-actions right-must highlighted-area">
        <h2>${_("Reviewing")}</h2>
        <div class="status ${statusClass}" title="${_("Call for papers")}">${statusText}</div>
        <ul>
            % if showSubmit:
                <li id="rev-submit"><a id="revSubmit" class="i-button icon-upload" href="#">${prefixUpload}Upload paper</a></li>
            % endif
            % if showHistory and len(Contribution.getReviewManager().getVersioning()) > 1:
                <li><a id="revHistory" href="#">${_("History")}</a></li>
            % endif
            % if showMaterial:
                <li><a id="revMaterial" href="#">${_("View Paper")}</a></li>
            % endif

        </ul>
    </div>
    % endif
</%block>

<%block name="place">
    <% import MaKaC.webinterface.linking as linking %>
    <% location = Contribution.getLocation() %>
    <% room = Contribution.getRoom() %>
    % if location or room:
    <div class="place">
        % if location:
            <span>
                ${location.getName()}
                % if room:
                    % if location.getName():
                     -
                    % endif
                    ${linking.RoomLinker().getHTMLLink(room,location)}
                % endif
            </span>
        % endif
    </div>
    % endif
</%block>

<%block name="authors">
    <div class="column">
    % if Contribution.getPrimaryAuthorList():
        <h2>${_("Primary authors")}</h2>
        <ul>
        % for pa in Contribution.getPrimaryAuthorList():
            <li class="icon-user">
                <a href="${getAuthorURL(pa)}">${pa.getDirectFullName()}</a> (${pa.getAffiliation()})
            </li>
        % endfor
        </ul>
    % endif
    </div>
</%block>

<%block name="coauthors">
    <div class="column">
    % if Contribution.getCoAuthorList():
        <h2>${_("Co-authors")}</h2>
        <ul>
        % for ca in Contribution.getCoAuthorList():
            <li class="icon-user">
                <a href="${getAuthorURL(ca)}">${ca.getDirectFullName()}</a> (${ca.getAffiliation()})
            </li>
        % endfor
        </ul>
    % endif
    </div>
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
        var popupAuthors = new AuthorsPopup($T("Primary authors"), ${fossilize(Contribution.getPrimaryAuthorList()) | n,j}, '${Contribution.getConference().getId()}', '${Contribution.getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}', function() {self.popupAllowClose = true; return true;});
        popupAuthors.open();
    });

    $("#moreCoAuthors").click(function(){
        var popupCoAuthors = new AuthorsPopup($T("Co authors"), ${fossilize(Contribution.getCoAuthorList()) | n,j}, '${Contribution.getConference().getId()}', '${Contribution.getId()}', '${Contribution.getSession().getId() if Contribution.getSession() else ""}', function() {self.popupAllowClose = true; return true;});
        popupCoAuthors.open();
    });

    $("#revSubmit").click(function(e){
        e.preventDefault();
        var popupSubmit = new SubmitPopup($T("Paper selection and submission"), args);
        popupSubmit.open();
    });

    $("#revMaterial").click(function(e){
        e.preventDefault();
        var killProgress = IndicoUI.Dialogs.Util.progress();
        jsonRpc(Indico.Urls.JsonRpcService, "material.reviewing.list", args,
                function(result, error){
                    killProgress();
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                    } else {
                        var popupMaterial = new UploadedPaperPopup($T("Submitted paper"), result.reviewing?result.reviewing.resources:{});
                        popupMaterial.open();
                    }
        });
    });

    $("#revHistory").click(function(e){
        e.preventDefault();
        var killProgress = IndicoUI.Dialogs.Util.progress();
            jsonRpc(Indico.Urls.JsonRpcService, "contribution.review.getReviewHistory",
                    {confId: '${Contribution.getConference().getId()}',
                     contribId: '${Contribution.getId()}'},
                    function(result, error){
                        killProgress();
                        if (exists(error)) {
                            IndicoUtil.errorReport(error);
                        } else {
                            var popup = new ExclusivePopupWithButtons($T('Review History'), null, false, false, true);
                            popup._getButtons = function() {
                                return [
                                    [$T('Close'), function() {
                                        popup.close();
                                    }]
                                ];
                            };
                            popup.draw = function() {
                                this.ExclusivePopupWithButtons.prototype.draw.call(this, $("<div/>").css({'max-height':'550px', 'min-width':'500px', 'max-width':'800px'}).append(result), {});
                            };
                            popup.open();
                        }
            });
        });

    $(".contributionSectionContent").mathJax();
</script>
</%block>
