% if not RecordingCapable:
<div style="margin-bottom: 1em;">
    % if RecordingCapableRooms:
    <table>
        <tr>
            <td>
                <span class="RRNoteTitle">${"Note:" | _}</span>
            </td>
            <td>
                <span class="RRNoteText">
                    ${_("In order to send a Recording request, you need to select a room capable of recording. ")}
                    <span class='fakeLink' onclick='toggleRecordingCapableRooms();' id="recordingRoomsText">${"See list of record-able rooms" | _}</span>
                </span>
            </td>
        </tr>
        <tr>
            <td></td>
            <td>
                <div id="recordingCapableRoomsDiv" style="display:none;">
                    <div style="padding-top:15px;padding-bottom:15px;">
                        <span class="RRNoteText">${"These are the rooms capable of recording:" | _} </span>
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
                            ${"But please remember, you have to book it as well!" | _}
                        </span>
                    </div>
                </div>
            </td>
        </tr>
    </table>
    % else:
    <div>
        <span class="RRNoteTitle">${"Note:" | _}</span>
        <span class="RRNoteText">
            ${_("In order to send a Recording Request you need to select a room capable of recording. However there are none currently marked as capable in the database.")}
        </span>
    </div>
    % endif
</div>
% else:
<div style="margin-bottom: 1em;">
    <span class="RRNoteTitle">${"Note:" | _}</span>
    <span class="RRNoteText">
        ${_("If you have not done so already, please remember to book your room(s).")}
    </span>
</div>
% endif

<div id="RRForm">

    % if IsSingleBooking:
    <div style="margin-bottom: 1em;">
        <div id="sendRecordingRequestTop" style="display:none;">
            <button onclick="send('RecordingRequest')">${ "Send request" | _ }</button>
            ${inlineContextHelp(_('Send the Request to the Recording administrators.'))}
        </div>
        <div id="modifyRecordingRequestTop" style="display:none;">
            <button onclick="send('RecordingRequest')">${ "Modify request" | _}</button>
            ${inlineContextHelp(_('Modify the Recording Request.'))}
        </div>
        <div id="withdrawRecordingRequestTop" style="display:none;">
            <button onclick="withdraw('RecordingRequest')">${ 'Withdraw request' | _ }</button>
            ${inlineContextHelp(_('Withdraw the Recording Request.'))}
        </div>
    </div>
    % endif


    <!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
        <!-- WHICH CONTRIBUTIONS SHOULD BE RECORDED -->
    % if not IsLecture:
    <div class="RRFormSection">
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Which talks would you like to have recorded?' | _ }</span>
             <table>
                <tr>
                    <td>
                        <input type="radio" name="talks" value="all" id="allTalksRB" onclick="RR_hideTalks()" checked />
                    </td>
                    <td>
                        % if NTalks == NWebcastCapableContributions:
                        <label for="allTalksRB" id="allTalksRBLabel" >All talks</label>
                        % else:
                        <label for="allTalksRB" id="allTalksRBLabel">${"All record-able talks." | _}</label>
                    </td>
                </tr>
                            % if RecordingCapable:
                <tr>
                    <td></td>
                    <td>
                        <span class="RRNoteTitle">${"Note:" | _}</span>
                        <span class="RRNoteText">
                            ${_("Some of your talks (%d out of %d) are not in a room capable of recording and thus cannot be recorded.") % (NTalks - NRecordingCapableContributions, NTalks)}
                        </span>
                        <span class='fakeLink' onclick='toggleRecordingCapableRooms();' id="recordingRoomsText">${"See list of record-able rooms" | _}</span>
                        <div id="recordingCapableRoomsDiv" style="display:none;">
                            <div style="padding-top:15px;padding-bottom:15px;">
                                <span class="RRNoteText">${"These are the rooms capable of recording:" | _} </span>
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
                                    ${"But please remember, you have to book the rooms as well!" | _}
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
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${"Choose talks." | _}</label>
                        % else:
                        <label for="chooseTalksRB" id="chooseTalksRBLabel">${"Choose among record-able talks." | _}</label>
                        % endif
                    </td>
                </tr>
            </table>
        </div>

        <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
        <div id="contributionsDiv" class="RRFormSubsection" style="display: ${ displayText };">
            <span class="WRQuestion">${"Please choose among the record-able contributions below:" | _}</span>

            % if HasRecordingCapableTalks:
            <span class="fakeLink" style="margin-left: 20px;" onclick="RRSelectAllContributions()">${"Select all" | _}</span>
            <span class="horizontalSeparator">|</span>
            <span class="fakeLink" onclick="RRUnselectAllContributions()">${"Select none" | _}</span>
            % endif

            <div class="RRContributionListDiv">
                <ul class="RROptionList" id="contributionList">
                </ul>
            </div>
        </div>

        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Please write here additional comments about talk selection:' | _ }</span>
            <input size="60" type="text" name="talkSelectionComments" style="display:block;">
        </div>
    </div>
    % endif

    <div class="RRFormSection">
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Do you commit to ensure that the speakers will give their permission to have their talks recorded?' | _ }</span>
            <br/>
            <input type="radio" name="permission" id="permissionYesRB" value="Yes" >
            <label for="permissionYesRB" id="permissionYesRBLabel">${ 'Yes' | _ }</label>
            <input type="radio" name="permission" id="permissionNoRB"value="No" >
            <label for="permissionNoRB" id="permissionNoRBLabel">${ 'No' | _ }</label>
            ${'<span style="margin-left: 2em;">'+ ConsentForm +'</span>' if ConsentForm else ""}
        </div>
    </div>

    <!-- DRAW BOX AROUND SECTION 2: TECHNICAL DETAILS FOR RECORDING -->
    <div class="RRFormSection">
        <!-- SLIDES? CHALKBOARD? -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Will slides and/or chalkboards be used?' | _ }</span>
            <br />
            <select name="lectureOptions" id="lectureOptions">
                <option value="chooseOne">-- ${ 'Choose one' | _ } --</option>
                % for value, text in LectureOptions:
                <option value="${value}">${text}</option>
                % endfor
            </select>
        </div>

        <!-- WHAT TYPE OF TALK IS IT -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'What type of event is it?' | _ }</span>
            <br />
            <select name="lectureStyle" id="lectureStyle">
                <option value="chooseOne">-- ${ 'Choose one' | _ } --</option>
                % for value, text in TypesOfEvents:
                <option value="${value}">${text}</option>
                % endfor
            </select>
        </div>

        <!-- HOW URGENTLY IS POSTING NEEDED -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'How urgently do you need to have the recordings posted online?' | _ }</span>
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
            <span class="RRQuestion">${ 'How many people do you expect to view the online recordings afterward?' | _ }</span>
            <br />
            <input type="text" size="20" name="numRemoteViewers" value="" />
        </div>

        <!-- HOW MANY ATTENDEES -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'How many people do you expect to attend the event in person?' | _ }</span>
            <br />
            <input type="text" size="20" name="numAttendees" value="" />
        </div>
    </div>

    <!-- DRAW BOX AROUND SECTION 3: METADATA AND SURVEY INFO -->
    <div class="RRFormSection">
        <!-- PURPOSE OF RECORDING -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Why do you need this event recorded? (check all that apply)' | _ }</span>
            <ul class="RROptionList">
                % for value, text in RecordingPurpose:
                <li>
                    <input type="checkbox" name="recordingPurpose" value="${value}" id="${value}CB">
                    <label for="${value}CB">${text}</label>
                </li>
                % endfor
            </ul>
        </div>
        <!-- EXPECTED AUDIENCE -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Who is the intended audience? (check all that apply)' | _ }</span>
            <ul class="RROptionList">
                % for value, text in IntendedAudience:
                <li>
                    <input type="checkbox" name="intendedAudience" value="${value}" id="${value}CB">
                    <label for="${value}CB">${text}</label>
                </li>
                % endfor
            </ul>
        </div>
        <!-- SUBJECT MATTER -->
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'What is the subject matter? (check all that apply)' | _ }</span>
            <ul class="RROptionList">
                % for value, text in SubjectMatter:
                <li>
                    <input type="checkbox" name="subjectMatter" value="${value}" id="${value}CB">
                    <label for="${value}CB">${text}</label>
                </li>
                % endfor
            </ul>
        </div>
    </div>

    <!-- SECTION 4: Extra comments -->
    <div class="RRFormSection">
        <div class="RRFormSubsection">
            <span class="RRQuestion">${ 'Please write here any other comments or instructions you may have:' | _ }</span>
            <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
        </div>
    </div>

    % if IsSingleBooking:
    <div style="margin-top: 1em;">
        <div id="sendRecordingRequestBottom" style="display:none;">
            <button onclick="send('RecordingRequest')">${ 'Send request' | _ }</button>
            ${inlineContextHelp(_('Send the Request to the Recording administrators.'))}
        </div>
        <div id="modifyRecordingRequestBottom" style="display:none;">
            <button onclick="send('RecordingRequest')">${ 'Modify request' | _ }</button>
            ${inlineContextHelp(_('Modify the Recording Request.'))}
        </div>
        <div id="withdrawRecordingRequestBottom" style="display:none;">
            <button onclick="withdraw('RecordingRequest')">${ 'Withdraw request' | _ }</button>
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

