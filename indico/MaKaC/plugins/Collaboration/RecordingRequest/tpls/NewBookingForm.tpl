<% declareTemplate(newTemplateStyle=True) %>

<% if not HasLocation: %>
<div style="margin-bottom: 1em;">
    <span class="RRNoteTitle"><%=_("Warning:")%></span>
    <span class="RRNoteText">
        <%= _("We will need to know the location before we can record the event.") %><br />
        <%= _("Please go to the") %> <a href="<%= urlHandlers.UHConferenceModification.getURL(Conference)%>"> <%= _("General Settings") %></a> <%= _("and enter the room location(s) for this Indico event.")%>
    </span>
</div>
<% end %>

<% if IsSingleBooking: %>
<div style="margin-bottom: 1em;">
    <div id="sendRecordingRequestTop" style="display:none;">
        <button onclick="send('RecordingRequest')">Send request</button>
        <% inlineContextHelp(_('Send the Request to the Recording administrators.')) %>
    </div>
    <div id="modifyRecordingRequestTop" style="display:none;">
        <button onclick="send('RecordingRequest')">Modify request</button>
        <% inlineContextHelp(_('Modify the Recording Request.')) %>
    </div>
    <div id="withdrawRecordingRequestTop" style="display:none;">
        <button onclick="withdraw('RecordingRequest')">Withdraw request</button>
        <% inlineContextHelp(_('Withdraw the Recording Request.')) %>
    </div>
</div>
<% end %>


<!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
<div class="RRFormSection">
    <!-- WHICH CONTRIBUTIONS SHOULD BE RECORDED -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">Which talks would you like to have recorded?</span>
        <div>
            <input type="radio" name="talks" value="all" id="allTalksRB" onclick="RR_hideTalks()" checked>
            <label for="allTalksRB">All talks</label>
            <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="RR_loadTalks()">
            <label for="chooseTalksRB">Choose</label>
            <input type="radio" name="talks" value="neither" id="neitherRB" onclick="RR_hideTalks()">
            <label for="neitherRB">Neither, see comment</label>
        </div>
    </div>
    <% displayText = ('none', 'block')[DisplayTalks and InitialChoose] %>
    <div id="contributionsDiv" class="RRFormSubsection" style="display: <%= displayText %>;">
        <span class="RRQuestion">Please choose among the contributions below:</span>
        <% if not HasTalks: %>
        <div>
            <span style="padding-left: 20px;"><%= _("This event has no talks.") %></span>
        </div>
        <% end %>
        
        <% if HasTalks: %>
        <span class="fakeLink" style="margin-left: 20px;" onclick="WRSelectAllContributions()">Select all</span>
        <span class="horizontalSeparator">|</span>
        <span class="fakeLink" onclick="WRUnselectAllContributions()">Select none</span>
        <% end %>
        
        <div class="RRContributionListDiv">
            <table>
                <tr id="contributionsRow">
                    <% if DisplayTalks: %>
                        <% if HasTalks: %>
                            <% for cl in TalkLists: %>
                            <td class="RRContributionsColumn">
                                <ul class="RROptionList">
                                <% for talk, checked in cl: %>
                                    <% checkedText = ('', 'checked')[checked] %>
                                    <li>
                                        <input type="checkbox" name="talkSelection" value="<%= talk.getId() %>" id="talk<%=talk.getId()%>CB"/ <%=checkedText%>>
                                        <label for="contribution<%=talk.getId()%>CB">
                                            <span class="RRContributionId">[<%= talk.getId() %>]</span>
                                            <span class="RRContributionName"><%= talk.getTitle() %></span>
                                            <% if talk.getSpeakerList() : %>
                                            <span class="RRSpeakers">, by <%= " and ".join([person.getFullName() for person in talk.getSpeakerList()]) %></span>
                                            <% end %>
                                            <% if talk.getLocation(): %>
                                                <% locationText = " (" + talk.getLocation().getName() %>
                                                <% if talk.getRoom(): %>
                                                    <% locationText += ", " + talk.getRoom().getName() + ")" %> 
                                                <% end %>
                                                <span class="WRSpeakers"><%= locationText %></span>
                                            <% end %>
                                        </label>
                                    </li>
                                <% end %>
                                </ul>
                            </td>
                            <% end %>
                        <% end %>
                    <% end%>
                </tr>
            </table>
        </div>
        <% if HasTalks: %>
        <script type="text/javascript">
            var WRSelectAllContributions = function() {
                each($N('talkSelection'), function(checkbox) {
                    checkbox.dom.checked = true;
                });
            }
            var WRUnselectAllContributions = function() {
                each($N('talkSelection'), function(checkbox) {
                    checkbox.dom.checked = false;
                });
            }
        </script>
        <% end %>
    </div>
    <div class="RRFormSubsection">
        <span class="RRQuestion">Please write here additional comments about talk selection:</span>
        <input size="60" type="text" name="talkSelectionComments" style="display:block;">
    </div>
    <div class="RRFormSubsection">
        <span class="RRQuestion">Have all the speakers given permission to have their talks recorded?</span>
        <br/>
        <input type="radio" name="permission" id="permissionYesRB" value="Yes" >
        <label for="permissionYesRB" id="permissionYesRBLabel">Yes</label>
        <input type="radio" name="permission" id="permissionNoRB"value="No" >
        <label for="permissionNoRB" id="permissionNoRBLabel">No</label>
        <span style="margin-left: 2em;">Here is the <a href="<%= ConsentFormURL %>">Recording Consent Form</a> to be signed by each speaker.</span>
    </div>
</div>

<!-- DRAW BOX AROUND SECTION 2: TECHNICAL DETAILS FOR RECORDING -->
<div class="RRFormSection">
    <!-- SLIDES? CHALKBOARD? -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">Will slides and/or chalkboards be used?</span>
        <br />
        <select name="lectureOptions" id="lectureOptions">
            <option value="chooseOne">-- Choose one --</option>
            <% for value, text in LectureOptions:%>
            <option value="<%=value%>"><%=text%></option>
            <% end %>
        </select>
    </div>
    
    <!-- WHAT TYPE OF TALK IS IT -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">What type of event is it?</span>
        <br />
        <select name="lectureStyle" id="lectureStyle">
            <option value="chooseOne">-- Choose one --</option>
            <% for value, text in TypesOfEvents:%>
            <option value="<%=value%>"><%=text%></option>
            <% end %>
        </select>
    </div>

    <!-- HOW URGENTLY IS POSTING NEEDED -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">How urgently do you need to have the recordings posted online?</span>
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
        <span class="RRQuestion">How many people do you expect to view the online recordings afterward?</span>
        <br />
        <input type="text" size="20" name="numRemoteViewers" value="" />
    </div>

    <!-- HOW MANY ATTENDEES -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">How many people do you expect to attend the event in person?</span>
        <br />
        <input type="text" size="20" name="numAttendees" value="" />
    </div>

</div>

<!-- DRAW BOX AROUND SECTION 3: METADATA AND SURVEY INFO -->
<div class="RRFormSection">
    <!-- PURPOSE OF RECORDING -->
    <div class="RRFormSubsection">
        <span class="RRQuestion">Why do you need this event recorded? (check all that apply)</span>
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
        <span class="RRQuestion">Who is the intended audience? (check all that apply)</span>
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
        <span class="RRQuestion">What is the subject matter? (check all that apply)</span>
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
        <span class="RRQuestion">Please write here any other comments or instructions you may have:</span>
        <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
    </div>
</div>

<% if IsSingleBooking: %>
<div style="margin-top: 1em;">
    <div id="sendRecordingRequestBottom" style="display:none;">
        <button onclick="send('RecordingRequest')">Send request</button>
        <% inlineContextHelp(_('Send the Request to the Recording administrators.')) %>
    </div>
    <div id="modifyRecordingRequestBottom" style="display:none;">
        <button onclick="send('RecordingRequest')">Modify request</button>
        <% inlineContextHelp(_('Modify the Recording Request.')) %>
    </div>
    <div id="withdrawRecordingRequestBottom" style="display:none;">
        <button onclick="withdraw('RecordingRequest')">Withdraw request</button>
        <% inlineContextHelp(_('Withdraw the Recording Request.')) %>
    </div>
</div>
<% end %>

<script type="text/javascript">
    var RR_contributionsLoaded = <%= jsBoolean(DisplayTalks or not HasTalks) %>;
</script>