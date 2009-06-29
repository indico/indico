<% declareTemplate(newTemplateStyle=True) %>

<% if not Conference.getLocation(): %>
<!-- If no room entered, then warn them -->
<div style="margin-bottom: 1em;">
    <span class="RRWarningMessage">
        <u>Warning:</u> We will need to know the location before we can record the event.<br/>
        Please go to the <a href="<%= urlHandlers.UHConferenceModification.getURL(Conference)%>">main tab</a> and enter the room location(s) for this Indico event
    </span>
</div>
<% end %>

<% if IsSingleBooking: %>
<div style="margin-bottom: 1em;">
    <button name="sendRecordingRequest" onclick="send('RecordingRequest')" style="display:none;">Send request</button>
    <button name="modifyRecordingRequest" onclick="send('RecordingRequest')" style="display:none;">Modify request</button>
    <button name="withdrawRecordingRequest" onclick="withdraw('RecordingRequest')" style="display:none;">Withdraw request</button>
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
    <div id="contributionsDiv" class="RRFormSubsection" style="display: none;">
        <span class="RRQuestion">Please choose among the contributions below:</span>
        <div class="RRContributionListDiv">
            <table>
                <tr id="contributionsRow">
                    <% if DisplayContributions: %>
                        <% if HasContributions: %>
                            <% for cl in ContributionLists: %>
                            <td class="RRContributionsColumn">
                                <ul class="RROptionList">
                                <% for contribution, checked in cl: %>
                                    <% if checked: %>
                                        <% checkedText = 'checked' %>
                                    <% end %>
                                    <% else: %>
                                        <% checkedText = '' %>
                                    <% end %>
                                    <li>
                                        <input type="checkbox" name="talkSelection" value="<%= contribution.getId() %>" id="contribution<%=contribution.getId()%>CB"/ <%=checkedText%>>
                                        <label for="contribution<%=contribution.getId()%>CB">
                                            <span class="RRContributionId">[<%= contribution.getId() %>]</span>
                                            <span class="RRContributionName"><%= contribution.getTitle() %></span>
                                            <% if contribution.getSpeakerList() : %>
                                            <span class="RRSpeakers">, by <%= " and ".join([person.getFullName() for person in contribution.getSpeakerList()]) %></span>
                                            <% end %>
                                        </label>
                                    </li>
                                <% end %>
                                </ul>
                            </td>
                            <% end %>
                        <% end %>
                        <% else: %>
                            <td class="RRContributionsColumn" style="padding-left: 20px;">
                                This conference has currently no talks.
                            </td>
                        <% end %>
                    <% end%>
                </tr>
            </table>
        </div>
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
    <button name="sendRecordingRequest" onclick="send('RecordingRequest')" style="display:none;">Send request</button>
    <button name="modifyRecordingRequest" onclick="send('RecordingRequest')" style="display:none;">Modify request</button>
    <button name="withdrawRecordingRequest" onclick="withdraw('RecordingRequest')" style="display:none;">Withdraw request</button>
</div>
<% end %>
