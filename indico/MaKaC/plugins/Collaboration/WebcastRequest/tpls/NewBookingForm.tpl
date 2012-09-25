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
                    <span class='fakeLink' onclick='toggleWebcastCapableRooms();' id="webcastRoomsText">${_("See list of webcast-able rooms")}</span>
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


    <!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
% if not IsLecture:
    <div class="WRFormSection" id="contributionselectionDiv">
        <!-- WHICH CONTRIBUTIONS SHOULD BE WEBCASTED -->
        <div class="WRFormSubsection">
            <span class="WRQuestion">Which talks would you like to have webcasted?</span>
            <table>
                <tr>
                    <td>
                        <input type="radio" name="talks" value="all" id="allTalksRB" onclick="WR_hideTalks()" checked />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="allTalksRB" id="allTalksRBLabel" >All talks</label>
                        % else:
                        <label for="allTalksRB" id="allTalksRBLabel">${_("All webcast-able talks.")}</label>
                    </td>
                </tr>
                            % if WebcastCapable:
                <tr>
                    <td></td>
                    <td>
                        <span class="WRNoteTitle">${_("Note:")}</span>
                        <span class="WRNoteText">
                            ${_("Some of your talks")} (${ str(NTalks - NWebcastCapableContributions) + _(" out of ") + str(NTalks) }) ${_(" are not in a room capable of webcasting and thus cannot be webcasted.")}
                        </span>
                        <span class='fakeLink' id="webcastTalksText">${_("See list of webcast-able talks")}</span> |
                        <span class='fakeLink' id="webcastRoomsText">${_("See list of webcast-able rooms")}</span>
                        <div id="webcastCapableTalksDiv" style="display:none;">
                            <div style="padding-top:15px;padding-bottom:15px;">
                                <span class="WRNoteText">${_("These are the talks capable of being webcasted:")} </span>
                                <ul class="WROptionList" style="margin-left: 18px; font-size: 13px" id="contributionWebcastedList">
                                </ul>
                            </div>
                         </div>
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
                            % endif
                    </td>
                </tr>
                        % endif
                <tr>
                    <td>
                        <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="WR_loadTalks()" />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose talks.")}</label>
                        % else:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose among webcast-able talks.")}</label>
                        % endif
                    </td>
                </tr>
            </table>
        </div>

        <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
        <div id="contributionsDiv" class="WRFormSubsection" style="display: ${ displayText };">
            <span class="WRQuestion">${_("Please choose among the webcast-able contributions below:")}</span>

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

    <div class="WRFormSubsection">
        <span class="WRQuestion">${_("Please select the audience of the webcast:")}</span>
        <div>
            <select name="audience">
                <option value="">${_("Public")}</option>
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

<script type="text/javascript">
    var isLecture = ${ jsBoolean(IsLecture) };
    var WRWebcastCapable = ${ jsBoolean(WebcastCapable) };
    var WR_contributions = ${ jsonEncode(Contributions) };
    var NWebcastCapableContributions = ${NWebcastCapableContributions};
    var NTalks = ${NTalks};
    var WR_contributionsLoaded = ${ jsBoolean(DisplayTalks or not HasWebcastCapableTalks) };

% if (not WebcastCapable and WebcastCapableRooms) or (NTalks > NWebcastCapableContributions and WebcastCapable):
    function showRooms(){
    $("#webcastRoomsText").text($T("Hide list of webcast-able rooms."));
    $("#webcastCapableRoomsDiv").show();
    if(!$("#webcastCapableTalksDiv").is(":hidden")) hideTalks();
    };
    function hideRooms(){
        $("#webcastRoomsText").text($T("See list of webcast-able rooms."));
        $("#webcastCapableRoomsDiv").hide();
    };
    function showTalks(){
        $("#webcastTalksText").text($T("Hide list of webcast-able talks."));
        $("#webcastCapableTalksDiv").show();
        if(!$("#webcastCapableRoomsDiv").is(":hidden")) hideRooms();
    };
    function hideTalks(){
        $("#webcastTalksText").text($T("See list of webcast-able talks."));
        $("#webcastCapableTalksDiv").hide();
    };
    $("#webcastRoomsText").click( function () {
        $('#webcastCapableRoomsDiv').is(':hidden')?showRooms():hideRooms();
    });
    $("#webcastTalksText").click( function () {
        $('#webcastCapableTalksDiv').is(':hidden')?showTalks():hideTalks();
    });
% endif
</script>