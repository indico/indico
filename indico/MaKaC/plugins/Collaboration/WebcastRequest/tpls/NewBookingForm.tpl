% if not WebcastCapable:
<div style="margin-bottom: 1em;">
    % if WebcastCapableRooms:
    <table>
        <tr>
            <td>
                <span class="WRNoteTitle">${_("Note:")}</span>
            </td>
            <td>
                <span class="WRNoteText">
                    ${_("In order to send a Webcast request, you need to select a room capable of webcasting. ")}
                    <span class='fakeLink' onclick='toggleWebcastCapableRooms();' id="webcastRoomsText">${_("See list of webcastable rooms")}</span>
                </span>
            </td>
        </tr>
        <tr>
            <td></td>
            <td>
                <div id="webcastCapableRoomsDiv" style="display:none;">
                    <div style="padding-top:15px;padding-bottom:15px;">
                        <span class="WRNoteText">${_("These are the rooms capable of webcasting:")} </span>
                        <table style="margin-left: 20px;">
                            % for roomName in WebcastCapableRooms:
                                <tr>
                                    <td>
                                        ${roomName.split(":")[0] }:
                                    </td>
                                    <td>
                                        ${roomName.split(":")[1] }
                                    </td>
                                </tr>
                            % endfor
                        </table>
                        <span style="font-style: italic;">
                            ${_("Please go to the")} <a href="${ urlHandlers.UHConferenceModification.getURL(Conference)}">${_("General settings")}</a> ${_("and select one of these room locations for this Indico event. ")}
                            ${_("But please remember, you have to book it as well!")}
                        </span>
                    </div>
                </div>
            </td>
        </tr>
    </table>
    % else:
    <div>
        <span class="WRNoteTitle">${_("Note:")}</span>
        <span class="WRNoteText">
            ${_("In order to send a Webcast Request you need to select a room capable of webcasting. However there are not currently marked as capable in the database.")}
        </span>
    </div>
    % endif
</div>
% else:
<div style="margin-bottom: 1em;">
    <span class="WRNoteTitle">${_("Note:")}</span>
    <span class="WRNoteText">
        ${_("If you have not done so already, please remember to book your room(s).")}
    </span>
</div>
% endif


% if IsLecture or NTalks > 0:
<div id="WRForm">

    % if IsSingleBooking:
    <div style="margin-bottom: 1em;">
        <div id="sendWebcastRequestTop" style="display:none;">
            <button onclick="send('WebcastRequest')">${_("Send request")}</button>
            ${inlineContextHelp(_('Send the Request to the Webcast administrators.'))}
        </div>
        <div id="modifyWebcastRequestTop" style="display:none;">
            <button onclick="send('WebcastRequest')">${_("Modify request")}</button>
            ${inlineContextHelp(_('Modify the Webcast Request.'))}
        </div>
        <div id="withdrawWebcastRequestTop" style="display:none;">
            <button onclick="withdraw('WebcastRequest')">${_("Withdraw request")}</button>
            ${inlineContextHelp(_('Withdraw the Webcast Request.'))}
        </div>
    </div>
    % endif

    <div>
            <span style="color:#881122">${_("The webcast will not be broadcasted before all speakers have signed the %s (see Electronic Agreement tab)")%agreementName}</span>
    </div>

% endif

% if not IsLecture and NTalks == 0:
    <div class="warning-message-box">
        <div class="message-text">
            ${_("Only the  contributions can be webcasted and there is no contribution in this event. Please go to Timetable and start adding them")}
        </div>
    </div>
% endif

    <!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
% if not IsLecture and NTalks > 0:
    <div class="WRFormSection" id="contributionselectionDiv">
        <!-- WHICH CONTRIBUTIONS SHOULD BE WEBCASTED -->
        <div class="WRFormSubsection">
            <span class="WRQuestion">Which talks would you like to have webcasted?</span>
            <table>
                <tr>
                    <td>
                        <input type="radio" name="talks" value="all" id="allTalksRB" onclick="WR_hideTalks();" checked />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="allTalksRB" id="allTalksRBLabel" >All talks</label>
                        % else:
                        <label for="allTalksRB" id="allTalksRBLabel">${_("All webcast-able talks.")}</label>
                        % endif
                    </td>
                </tr>
                % if WebcastCapable and (NWebcastCapableContributions < NTalks):
                <tr>
                    <td></td>
                    <td class="warning" id="not_capable_warning">
                        <h3>${_("Note")}</h3>
                        <p>
                            ${_('<a class="uncapable">{1} of {0}</a> talks are not in a room capable of webcasting and thus cannot be webcasted.').format(NTalks, NTalks - NWebcastCapableContributions)}
                            % if NWebcastCapableContributions:
                              ${_('<a class="capable">The remaining {0}</a> will be webcasted').format(NWebcastCapableContributions)}
                            % endif
                        </p>
                        <p><a href="#" class='fakeLink' id="webcastRoomsText">${_("See list of webcastable rooms")}</a></p>
                        <div id="webcastCapableRoomsDiv" style="display:none;">
                            <div style="padding-top:15px;padding-bottom:15px;">
                                <span class="WRNoteText">${_("These are the rooms capable of webcasting:")} </span>
                                <table style="margin-left: 20px;">
                                    % for roomName in WebcastCapableRooms:
                                        <tr>
                                            <td>
                                                ${roomName.split(":")[0] }
                                            </td>
                                            <td>
                                                ${roomName.split(":")[1] }
                                            </td>
                                        </tr>
                                    % endfor
                                </table>
                                <span style="font-style: italic;">
                                    ${_("Please go to the")} <a href="${ urlHandlers.UHConfModifSchedule.getURL(Conference)}">${_("Timetable")}</a> ${_("and select one of these room locations for your contributions. ")}
                                    ${_("But please remember, you have to book the rooms as well!")}
                                </span>
                            </div>
                        </div>
                    </td>
                </tr>
                % endif
                <tr>
                    <td>
                        <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="WR_loadTalks(${isManager | n,j})" />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose talks.")}</label>
                        % else:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose among webcastable talks.")}</label>
                        % endif
                    </td>
                </tr>
            </table>
        </div>

        <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
        <div id="contributionsDiv" class="WRFormSubsection" style="display: ${ displayText };">
            % if HasWebcastCapableTalks:
            <span class="fakeLink" style="margin-left: 20px;" onclick="WRSelectAllContributions()">Select all</span>
            <span class="horizontalSeparator">|</span>
            <span class="fakeLink" onclick="WRUnselectAllContributions()">Select none</span>
            % endif

            <div class="WRContributionListDiv">
                <ul class="WROptionList" id="contributionList">
                </ul>
            </div>
        </div>
    </div>
% endif

% if IsLecture or NTalks > 0:
    <div class="WRFormSubsection">
        <span class="WRQuestion">${_("Please choose the restriction to apply to the webcast:")}</span>
        <div>
            <select name="audience">
                <option value="">${_("No restriction (the webcast is public, anyone can watch)")}</option>
                % for audience in Audiences:
                    <option value=${ quoteattr(audience['name']) }>${ audience['name'] }</option>
                % endfor
            </select>
        </div>
    </div>

    <!-- SECTION 2: Extra comments -->
    <div class="WRFormSection">
        <div class="WRFormSubsection">
            <span class="WRQuestion">${_("Please write here any other comments or instructions you may have:")}</span>
            <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
        </div>
    </div>


    % if IsSingleBooking:
    <div style="margin-top: 1em;">
        <div id="sendWebcastRequestBottom" style="display:none;">
            <button onclick="send('WebcastRequest')">${_("Send request")}</button>
            ${inlineContextHelp(_('Send the Request to the Webcast administrators.'))}
        </div>
        <div id="modifyWebcastRequestBottom" style="display:none;">
            <button onclick="send('WebcastRequest')">${_("Modify request")}</button>
            ${inlineContextHelp(_('Modify the Webcast Request.'))}
        </div>
        <div id="withdrawWebcastRequestBottom" style="display:none;">
            <button onclick="withdraw('WebcastRequest')">${_("Withdraw request")}</button>
            ${inlineContextHelp(_('Withdraw the Webcast Request.'))}
        </div>
    </div>
    % endif
</div>

% endif
<script type="text/javascript">
    var isLecture = ${ jsBoolean(IsLecture) };
    var WRWebcastCapable = ${ jsBoolean(WebcastCapable) };
    var WR_contributions = ${ jsonEncode(Contributions) };
    var WR_contributions_able = ${ jsonEncode(ContributionsAble) };
    var WR_contributions_unable = ${ jsonEncode(ContributionsUnable) };
    var NWebcastCapableContributions = ${NWebcastCapableContributions};
    var NTalks = ${NTalks};
    var WR_contributionsLoaded = ${ jsBoolean(DisplayTalks or not HasWebcastCapableTalks) };

% if (not WebcastCapable and WebcastCapableRooms) or (NTalks > NWebcastCapableContributions and WebcastCapable):

    function showRooms(){
        $("#webcastRoomsText").text($T("Hide list of webcastable rooms."));
        $("#webcastCapableRoomsDiv").show();
    };

    function hideRooms(){
        $("#webcastRoomsText").text($T("See list of webcastable rooms."));
        $("#webcastCapableRoomsDiv").hide();
    };

    $(function() {
        $("#webcastRoomsText").click(function() {
            if ($('#webcastCapableRoomsDiv').is(':hidden')) {
                showRooms();
            } else {
                hideRooms();
            }
        });

        $(".warning .capable").attr('href', '#').click(function() {
            new ContributionsPopup($T("Contributions that can be Webcasted"),WR_contributions_able, false, function() {self.popupAllowClose = true; return true;}, true).open();
            return false;
        });
        $(".warning .uncapable").attr('href', '#').click(function() {
            new ContributionsPopup($T("Contributions that can't be Webcasted"),WR_contributions_unable, false, function() {self.popupAllowClose = true; return true;}, false).open();
            return false;
        });
    });

% endif
</script>
