<% declareTemplate(newTemplateStyle=True) %>

<% if not HasRoom: %>
<div style="margin-bottom: 1em;">
    <span class="RRNoteTitle"><%=_("Warning:")%></span>
    <span class="RRNoteText">
        <%= _("We will need to know the location and room before we can record the event.") %><br />
        <%= _("Please go to the") %> <a href="<%= urlHandlers.UHConferenceModification.getURL(Conference)%>"> <%= _("General Settings") %></a> <%= _("and enter the location and room for this Indico event.")%>
    </span>
</div>
<% end %>

<% if IsSingleBooking: %>
<div style="margin-bottom: 1em;">
    <div id="sendRecordingRequestTop" style="display:none;">
        <button onclick="send('RecordingRequest')"><%= _('Send request') %></button>
        <% inlineContextHelp(_('Send the Request to the Recording administrators.')) %>
    </div>
    <div id="modifyRecordingRequestTop" style="display:none;">
        <button onclick="send('RecordingRequest')"><%= _('Modify request') %></button>
        <% inlineContextHelp(_('Modify the Recording Request.')) %>
    </div>
    <div id="withdrawRecordingRequestTop" style="display:none;">
        <button onclick="withdraw('RecordingRequest')"><%= _('Withdraw request') %></button>
        <% inlineContextHelp(_('Withdraw the Recording Request.')) %>
    </div>
</div>
<% end %>


<!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
<div class="RRFormSection">
    <!-- WHICH CONTRIBUTIONS SHOULD BE RECORDED -->
<% if not IsLecture: %>
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Which talks would you like to have recorded?') %></span>
        <div>
            <input type="radio" name="talks" value="all" id="allTalksRB" onclick="RR_hideTalks()" checked>
            <label for="allTalksRB"><%= _('All talks') %></label>
            <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="RR_loadTalks()">
            <label for="chooseTalksRB"><%= _('Choose') %></label>
            <input type="radio" name="talks" value="neither" id="neitherRB" onclick="RR_hideTalks()">
            <label for="neitherRB"><%= _('Neither, see comment') %></label>
        </div>
    </div>
    <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
    <div id="contributionsDiv" class="RRFormSubsection" style="display: <%= displayText %>;">
        <span class="RRQuestion"><%= _('Please choose among the contributions below:') %></span>

        <% if HasTalks: %>
        <span class="fakeLink" style="margin-left: 20px;" onclick="RRSelectAllContributions()"><%= _('Select all') %></span>
        <span class="horizontalSeparator">|</span>
        <span class="fakeLink" onclick="RRUnselectAllContributions()"><%= _('Select none') %></span>
        <% end %>

        <div class="RRContributionListDiv">
            <ul class="RROptionList" id="contributionList">
            </ul>
        </div>
    </div>
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Please write here additional comments about talk selection:') %></span>
        <input size="60" type="text" name="talkSelectionComments" style="display:block;">
    </div>
<% end %>
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Do you commit to ensure that the speakers will give their permission to have their talks recorded?') %></span>
        <br/>
        <input type="radio" name="permission" id="permissionYesRB" value="Yes" >
        <label for="permissionYesRB" id="permissionYesRBLabel"><%= _('Yes') %></label>
        <input type="radio" name="permission" id="permissionNoRB"value="No" >
        <label for="permissionNoRB" id="permissionNoRBLabel"><%= _('No') %></label>
        <br/>
        <span style="margin-left: 2em;"><%= _('Here is the') %> <a href="<%= ConsentFormURL %>"><%= _('Recording Consent Form') %></a> <%= _('to be signed by each speaker. Please have this form signed by each speaker and return it to the <a href="http://it-multimedia.web.cern.ch/it-multimedia/audiovisual/">Audiovisual Service</a> (<a href="http://building.web.cern.ch/map/building?bno=50">50-1-004</a>). We may not publish the recorded video if we do not get the signed release form.') %></span>
    </div>
</div>

<!-- DRAW BOX AROUND SECTION 2: TECHNICAL DETAILS FOR RECORDING -->
<div class="RRFormSection">
    <!-- SLIDES? CHALKBOARD? -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Will slides and/or chalkboards be used?') %></span>
        <br />
        <select name="lectureOptions" id="lectureOptions">
            <option value="chooseOne">-- <%= _('Choose one') %> --</option>
            <% for value, text in LectureOptions:%>
            <option value="<%=value%>"><%=text%></option>
            <% end %>
        </select>
    </div>

    <!-- WHAT TYPE OF TALK IS IT -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('What type of event is it?') %></span>
        <br />
        <select name="lectureStyle" id="lectureStyle">
            <option value="chooseOne">-- <%= _('Choose one') %> --</option>
            <% for value, text in TypesOfEvents:%>
            <option value="<%=value%>"><%=text%></option>
            <% end %>
        </select>
    </div>

    <!-- HOW URGENTLY IS POSTING NEEDED -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('How urgently do you need to have the recordings posted online?') %></span>
        <br />
        <select name="postingUrgency" id="postingUrgency">
            <% for value, text in PostingUrgency:%>
            <% if value == "withinWeek" : %>
                <% selectedText = "selected" %>
            <% end %>
            <% else: %>
                <% selectedText = "" %>
            <% end %>
            <option value="<%=value%>" <%=selectedText %>><%=text%></option>
            <% end %>
        </select>
    </div>

    <!-- HOW MANY REMOTE VIEWERS -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('How many people do you expect to view the online recordings afterward?') %></span>
        <br />
        <input type="text" size="20" name="numRemoteViewers" value="" />
    </div>

    <!-- HOW MANY ATTENDEES -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('How many people do you expect to attend the event in person?') %></span>
        <br />
        <input type="text" size="20" name="numAttendees" value="" />
    </div>

</div>

<!-- DRAW BOX AROUND SECTION 3: METADATA AND SURVEY INFO -->
<div class="RRFormSection">
    <!-- PURPOSE OF RECORDING -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Why do you need this event recorded? (check all that apply)') %></span>
        <ul class="RROptionList">
            <% for value, text in RecordingPurpose: %>
            <li>
                <input type="checkbox" name="recordingPurpose" value="<%=value%>" id="<%=value%>CB">
                <label for="<%=value%>CB"><%=text%></label>
            </li>
            <% end %>
        </ul>
    </div>
    <!-- EXPECTED AUDIENCE -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Who is the intended audience? (check all that apply)') %></span>
        <ul class="RROptionList">
            <% for value, text in IntendedAudience: %>
            <li>
                <input type="checkbox" name="intendedAudience" value="<%=value%>" id="<%=value%>CB">
                <label for="<%=value%>CB"><%=text%></label>
            </li>
            <% end %>
        </ul>
    </div>
    <!-- SUBJECT MATTER -->
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('What is the subject matter? (check all that apply)') %></span>
        <ul class="RROptionList">
            <% for value, text in SubjectMatter: %>
            <li>
                <input type="checkbox" name="subjectMatter" value="<%=value%>" id="<%=value%>CB">
                <label for="<%=value%>CB"><%=text%></label>
            </li>
            <% end %>
        </ul>
    </div>
</div>

<!-- SECTION 4: Extra comments -->
<div class="RRFormSection">
    <div class="RRFormSubsection">
        <span class="RRQuestion"><%= _('Please write here any other comments or instructions you may have:') %></span>
        <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
    </div>
</div>

<% if IsSingleBooking: %>
<div style="margin-top: 1em;">
    <div id="sendRecordingRequestBottom" style="display:none;">
        <button onclick="send('RecordingRequest')"><%= _('Send request') %></button>
        <% inlineContextHelp(_('Send the Request to the Recording administrators.')) %>
    </div>
    <div id="modifyRecordingRequestBottom" style="display:none;">
        <button onclick="send('RecordingRequest')"><%= _('Modify request') %></button>
        <% inlineContextHelp(_('Modify the Recording Request.')) %>
    </div>
    <div id="withdrawRecordingRequestBottom" style="display:none;">
        <button onclick="withdraw('RecordingRequest')"><%= _('Withdraw request') %></button>
        <% inlineContextHelp(_('Withdraw the Recording Request.')) %>
    </div>
</div>
<% end %>

<script type="text/javascript">
    var isLecture = <%= jsBoolean(IsLecture) %>;
    var RR_contributions = <%= jsonEncode(Contributions) %>;
    var RR_contributionsLoaded = <%= jsBoolean(DisplayTalks or not HasTalks) %>;
</script>