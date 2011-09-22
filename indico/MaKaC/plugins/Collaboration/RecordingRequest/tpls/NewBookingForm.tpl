% if not RecordingCapable:
<div style="margin-bottom: 1em;">
    % if RecordingCapableRooms:
    <table>
        <tr>
            <td>
                <span class="RRNoteTitle">${_("Note:")}</span>
            </td>
            <td>
                <span class="RRNoteText">
                    ${_("In order to send a Recording request, you need to select a room capable of recording. ")}
                    <span class='fakeLink' onclick='toggleRecordingCapableRooms();' id="recordingRoomsText">${_("See list of record-able rooms")}</span>
                </span>
            </td>
        </tr>
        <tr>
            <td></td>
            <td>
                <div id="recordingCapableRoomsDiv" style="display:none;">
                    <div style="padding-top:15px;padding-bottom:15px;">
                        <span class="RRNoteText">${_("These are the rooms capable of recording:")} </span>
                        <table style="margin-left: 20px;">
                            % for roomName in RecordingCapableRooms:
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
                            ${_('Please go to the <a href="%s">General settings</a> and select one of these room locations for this Indico event. ') % urlHandlers.UHConferenceModification.getURL(Conference)}
                            ${_("But please remember, you have to book it as well!")}
                        </span>
                    </div>
                </div>
            </td>
        </tr>
    </table>
    % else:
    <div>
        <span class="RRNoteTitle">${_("Note:")}</span>
        <span class="RRNoteText">
            ${_("In order to send a Recording Request you need to select a room capable of recording. However there are none currently marked as capable in the database.")}
        </span>
    </div>
    % endif
</div>
% else:
<div style="margin-bottom: 1em;">
    <span class="RRNoteTitle">${_("Note:")}</span>
    <span class="RRNoteText">
        ${_("If you have not done so already, please remember to book your room(s).")}
    </span>
</div>
% endif

<div id="RRForm">

    % if IsSingleBooking:
    <div style="margin-bottom: 1em;">
        <div id="sendRecordingRequestTop" style="display:none;">
            <button onclick="send('RecordingRequest')">${ _("Send request") }</button>
            ${inlineContextHelp(_('Send the Request to the Recording administrators.'))}
        </div>
        <div id="modifyRecordingRequestTop" style="display:none;">
            <button onclick="send('RecordingRequest')">${ _("Modify request") }</button>
            ${inlineContextHelp(_('Modify the Recording Request.'))}
        </div>
        <div id="withdrawRecordingRequestTop" style="display:none;">
            <button onclick="withdraw('RecordingRequest')">${ _('Withdraw request') }</button>
            ${inlineContextHelp(_('Withdraw the Recording Request.'))}
        </div>
    </div>
    % endif

    <div>
            <span style="color:#881122">${_("The recordings will not be published before all speakers have signed the %s (see Electronic Agreement tab)")%agreementName}</span>
    </div>



    <!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
        <!-- WHICH CONTRIBUTIONS SHOULD BE RECORDED -->
    % if not IsLecture:
    <div class="RRFormSection">
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ _('Which talks would you like to have recorded?') }</span>
             <table>
                <tr>
                    <td>
                        <input type="radio" name="talks" value="all" id="allTalksRB" onclick="RR_hideTalks()" checked />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="allTalksRB" id="allTalksRBLabel" >${_("All talks") }</label>
                        % else:
                        <label for="allTalksRB" id="allTalksRBLabel">${_("All record-able talks.")}</label>
                    </td>
                </tr>
                            % if RecordingCapable:
                <tr>
                    <td></td>
                    <td>
                        <span class="RRNoteTitle">${_("Note:")}</span>
                        <span class="RRNoteText">
                            ${_("Some of your talks (%d out of %d) are not in a room capable of recording and thus cannot be recorded.") % (NTalks - NRecordingCapableContributions, NTalks)}
                        </span>
                        <span class='fakeLink' onclick='toggleRecordingCapableRooms();' id="recordingRoomsText">${_("See list of record-able rooms")}</span>
                        <div id="recordingCapableRoomsDiv" style="display:none;">
                            <div style="padding-top:15px;padding-bottom:15px;">
                                <span class="RRNoteText">${_("These are the rooms capable of recording:")} </span>
                                <table style="margin-left: 20px;">
                                    % for roomName in RecordingCapableRooms:
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
                                    ${_('Please go to the <a href="%s">Timetable</a> and select one of these room locations for your contributions. ') % urlHandlers.UHConfModifSchedule.getURL(Conference)}
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
                        <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="RR_loadTalks()" />
                    </td>
                    <td>
                        % if NTalks == NRecordingCapableContributions:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose talks.")}</label>
                        % else:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${_("Choose among record-able talks.")}</label>
                        % endif
                    </td>
                </tr>
            </table>
        </div>

        <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
        <div id="contributionsDiv" class="RRFormSubsection" style="display: ${ displayText };">
            <span class="WRQuestion">${_("Please choose among the record-able contributions below:")}</span>

            % if HasRecordingCapableTalks:
            <span class="fakeLink" style="margin-left: 20px;" onclick="RRSelectAllContributions()">${_("Select all")}</span>
            <span class="horizontalSeparator">|</span>
            <span class="fakeLink" onclick="RRUnselectAllContributions()">${_("Select none")}</span>
            % endif

            <div class="RRContributionListDiv">
                <ul class="RROptionList" id="contributionList">
                </ul>
            </div>
        </div>
    </div>
    % endif

    <!-- DRAW BOX AROUND SECTION 2: TECHNICAL DETAILS FOR RECORDING -->
    <div class="RRFormSection">

        <!-- HOW URGENTLY IS POSTING NEEDED -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ _('How urgently do you need to have the recordings posted online?') }</span>
            <br />
            <select name="postingUrgency" id="postingUrgency">
                % for value, text in PostingUrgency:
                % if value == "withinWeek" :
                    <% selectedText = "selected" %>
                % else:
                    <% selectedText = "" %>
                % endif
                <option value="${value}" ${selectedText }>${text}</option>
                % endfor
            </select>
        </div>

        <!-- HOW MANY REMOTE VIEWERS -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ _('How many people do you expect to view the online recordings afterward?') }</span>
            <br />
            <input type="text" size="20" name="numRemoteViewers" value="" />
        </div>

        <!-- HOW MANY ATTENDEES -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ _('How many people do you expect to attend the event in person?') }</span>
            <br />
            <input type="text" size="20" name="numAttendees" value="" />
        </div>
    </div>

    <!-- SECTION 3: Extra comments -->
    <div class="RRFormSection">
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ _('Please write here any other comments or instructions you may have:') }</span>
            <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
        </div>
    </div>

    % if IsSingleBooking:
    <div style="margin-top: 1em;">
        <div id="sendRecordingRequestBottom" style="display:none;">
            <button onclick="send('RecordingRequest')">${ _('Send request') }</button>
            ${inlineContextHelp(_('Send the Request to the Recording administrators.'))}
        </div>
        <div id="modifyRecordingRequestBottom" style="display:none;">
            <button onclick="send('RecordingRequest')">${ _('Modify request') }</button>
            ${inlineContextHelp(_('Modify the Recording Request.'))}
        </div>
        <div id="withdrawRecordingRequestBottom" style="display:none;">
            <button onclick="withdraw('RecordingRequest')">${ _('Withdraw request') }</button>
            ${inlineContextHelp(_('Withdraw the Recording Request.'))}
        </div>
    </div>
    % endif
</div>
<script type="text/javascript">
    var isLecture = ${ jsBoolean(IsLecture) };
    var RRRecordingCapable = ${ jsBoolean(RecordingCapable) };
    var RR_contributions = ${ jsonEncode(Contributions) };
    var RR_contributionsLoaded = ${ jsBoolean(DisplayTalks or not HasRecordingCapableTalks) };
</script>


% if (not RecordingCapable and RecordingCapableRooms) or (NTalks > NRecordingCapableContributions and RecordingCapable):
<script type="text/javascript">
    var recordingSwitch = false;
    var toggleRecordingCapableRooms = function () {
        IndicoUI.Effect.toggleAppearance($E('recordingCapableRoomsDiv'));
        if (webcastSwitch) {
            $E("recordingRoomsText").dom.innerHTML = $T("See list of record-able rooms.");
        } else {
            $E("recordingRoomsText").dom.innerHTML = $T("Hide list of record-able rooms.");
        }
        recordingSwitch = !recordingSwitch;
    }
</script>
% endif

