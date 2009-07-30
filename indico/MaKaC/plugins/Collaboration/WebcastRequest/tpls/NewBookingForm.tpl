<% declareTemplate(newTemplateStyle=True) %>

<% if not WebcastCapable=="true": %>
<div style="margin-bottom: 1em;">
        <span class="WRNote"><u><b><%=_("Note:")%></b></u> <%=_("In order to send a webcastrequest you need to select a room capable of webcasting, click")%> 
            <span class='fakeLink' onclick='toogleWebcastCapableRooms();'><%=_("here")%></span>    
            <span id="webcastEventText"><%=_("to show more information")%></span><br/> 
        </span>
        <div id="webcastCapableRoomsDiv" style="visibility: hidden;">
        <span class="WRNote"><%=_("These are the rooms capable of webcasting:")%> </span>
        <table style="margin-left: 20px;margin-top: 5px;margin-bottom:20px">
        <% for roomName in WebcastCapableRooms:%>
            <tr><td><%=roomName.split(":")[0] %></td><td><%=roomName.split(":")[1] %></td></tr>
        <% end %>
        </table>
        <span style="font-style: italic;margin-left: 20px">
            <%=_("Please go to the")%> <a href="<%= urlHandlers.UHConferenceModification.getURL(Conference)%>"><%=_("General settings")%></a> <%=_("and select one of these room locations for this Indico event. ")%>
            <%=_("But remember, you have to book it as well!")%>
        </span>
        </div>
        <script type="text/javascript">
            var webcastCapableRoomsDiv = $E("webcastCapableRoomsDiv");
            var webcastCapableRoomsDivHeight=webcastCapableRoomsDiv.dom.offsetHeight;
            webcastCapableRoomsDiv.dom.style.height = '0';
            //webcastCapableRoomsDiv.dom.style.visibility = 'visible';
            webcastCapableRoomsDiv.dom.style.opacity = '0';
            var webcastSwitch = false;
            function toogleWebcastCapableRooms() {
                if (webcastSwitch) {
                    IndicoUI.Effect.slide("webcastCapableRoomsDiv", webcastCapableRoomsDivHeight); 
                    $E("webcastEventText").dom.innerHTML = $T("to show more information.");
                }else {
                    IndicoUI.Effect.slide("webcastCapableRoomsDiv", webcastCapableRoomsDivHeight); 
                    webcastCapableRoomsDiv.dom.style.visibility = 'visible';
                    $E("webcastEventText").dom.innerHTML = $T("to hide the information.");
                }
                webcastSwitch = !webcastSwitch;
            }
        </script>
</div>
<% end %>
<% else: %>
<div style="margin-bottom: 1em;">
    <span class="WRNote">
        <u><b><%=_("Note:")%></b></u> <%=_("If you have not done so already, please remember to book your room")%>
    </span>
</div>
<% end %>
<div id="WRForm">
    <% if IsSingleBooking: %>
    <div style="margin-bottom: 1em;">
        <div id="sendWebcastRequestTop" class="sendWebcastRequestDiv" style="display:none;">
            <button onclick="send('WebcastRequest')"><%=_("Send request")%></button>
        </div>
        <div id="modifyWebcastRequestTop" class="modifyWebcastRequestDiv" style="display:none;">
            <button onclick="send('WebcastRequest')"><%=_("Modify request")%></button>
        </div>
        <div id="withdrawWebcastRequestTop" class="withdrawWebcastRequestDiv" style="display:none;">
            <button onclick="withdraw('WebcastRequest')"><%=_("Withdraw request")%></button>
        </div>
    </div>
    <% end %>
    <% if NwebcastCapableContributions > 0: %>
        <!-- DRAW BOX AROUND SECTION 1: SELECT CONTRIBUTIONS -->
        <div class="WRFormSection" id="contributionselectionDiv">
            <!-- WHICH CONTRIBUTIONS SHOULD BE WEBCASTED -->
            <div class="WRFormSubsection">
                <span class="WRQuestion">Which talks would you like to have webcasted?</span>
                <div>
                    <input type="radio" name="talks" value="all" id="allTalksRB" onclick="WR_hideTalks()"/>
                    <label for="allTalksRB" id="allTalksRBLabel" >All talks</label><span id="allTalksRBTT"/>
                    <input type="radio" name="talks" value="choose" id="chooseTalksRB" onclick="WR_loadTalks()" />
                    <label for="chooseTalksRB" id="chooseTalksRBLabel">Choose</label><span id="chooseTalksTT"/>
                    <% if NContributions > NwebcastCapableContributions and NContributions > 0 : %>
                        <% if NwebcastCapableContributions > 0:%>
                            <span class="WRNote">
                                <br/><b><u><%=_("Note:")%></b></u> <%=_("Only ")%> <%=NwebcastCapableContributions %> <%=_(" out of ")%> <%=NContributions %> <%=_(" contributions are in a room capable of webcasting.")%>
                            </span>
                        <% end %>
                    <% end %>
                </div>
            </div>
            <div id="contributionsDiv" class="WRFormSubsection" style="display: none;">
                <span class="WRQuestion"><%=_("Please choose among the contributions below:")%></span>
                <div class="WRContributionListDiv">
                    <table>
                        <tr id="contributionsRow">
                            <% if HasContributions: %>
                                <% for cl in ContributionLists: %>
                                <td class="WRContributionsColumn">
                                    <ul class="WROptionList">
                                    <% for contribution,checked,webcastcapable in cl: %>
                                        <% if checked: %>
                                            <% checkedText = 'checked' %>
                                        <% end %>
                                        <% else: %>
                                            <% checkedText = '' %>
                                        <% end %>
                                        <% disapledText = '' %>
                                        <% if webcastcapable: %>
                                        <li>
                                            <input type="checkbox" name="talkSelection" value="<%= contribution.getId() %>" id="contribution<%=contribution.getId()%>CB"/ <%=checkedText%>> 
                                            <label for="contribution<%=contribution.getId()%>CB">
                                                <span class="WRContributionId">[<%= contribution.getId() %>]</span>
                                                <span class="WRContributionName"><%= contribution.getTitle() %></span>
                                                <% if contribution.getSpeakerList() : %>
                                                <span class="WRSpeakers">, by <%= " and ".join([person.getFullName() for person in contribution.getSpeakerList()]) %></span>
                                                <% end %>
                                            </label>
                                        </li>
                                        <% end %>
                                    <% end %>
                                    </ul>
                                </td>
                                <% end %>
                            <% end %>
                            <% else: %>
                                <td class="WRContributionsColumn" style="padding-left: 20px;">
                                <%=_("This event has currently no talks.")%>
                                </td>
                            <% end %>
                        </tr>
                    </table>
                </div>
            </div>
            <%if NwebcastCapableContributions== NContributions:%>
                <script type="text/javascript">
                    IndicoUI.Effect.disappear($E('contributionsDiv'));
                </script>
            <% end %>
            <% else: %>
                <script type="text/javascript">
                   IndicoUI.Effect.appear($E('contributionsDiv'));
                </script>
            <% end %>
            <div class="WRFormSubsection">
                <span class="WRQuestion"><%=_("Please write here additional comments about talk selection:")%></span>
                <div><input size="60" type="text" name="talkSelectionComments"><span id="talkSelectionCommentsTT"/></div>
            </div>
        </div>
    <% end %>
    <div class="WRFormSection">
        <div class="WRFormSubsection">
        <span class="WRQuestion"><%=_("Have all the speakers given permission to have their talks webcasted?")%></span>
        <br/>
        <input type="radio" name="permission" id="permissionYesRB" value="Yes" >
        <label for="permissionYesRB" id="permissionYesRBLabel">Yes</label>
        <input type="radio" name="permission" id="permissionNoRB"value="No" >
        <label for="permissionNoRB" id="permissionNoRBLabel">No</label>
        <span style="margin-left: 2em;"><%=_("Here is the ")%><a href="<%= ConsentFormURL %>"><%=_("Webcast Consent Form")%></a> <%=_("to be signed by each speaker.")%></span>
        </div>
    </div>
    <!-- DRAW BOX AROUND SECTION 2: TECHNICAL DETAILS FOR WEBCAST -->
    <div class="WRFormSection">
        <!-- SLIDES? CHALKBOARD? -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("Will slides and/or chalkboards be used?")%></span>
            <br />
            <select name="lectureOptions" id="lectureOptions">
                <option value="chooseOne">-- Choose one --</option>
                <% for value, text in LectureOptions:%>
                <option value="<%=value%>"><%=text%></option>
                <% end %>
            </select>
        </div>
        
        <!-- WHAT TYPE OF TALK IS IT -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("What type of event is it?")%></span>
            <br />
            <select name="lectureStyle" id="lectureStyle">
                <option value="chooseOne">-- Choose one --</option>
                <% for value, text in TypesOfEvents:%>
                <option value="<%=value%>"><%=text%></option>
                <% end %>
            </select>
        </div>
    
        <!-- HOW URGENTLY IS POSTING NEEDED -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("All webcasts are recorded. How soon do you need your recording posted online afterwards?")%></span>
            <br />
            <select name="postingUrgency" id="postingUrgency">
                <% for value, text in PostingUrgency:%>
                <% if value == "never" : %>
                    <% selectedText = "selected" %>
                <% end %>
                <% else: %>
                    <% selectedText = "" %>
                <% end %>
                <option value="<%=value%>" <%=selectedText %>><%=text%></option>
                <% end %>
            </select>
        </div>
    
       <!-- HOW MANY WEBCAST VIEWERS -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("How many people do you expect to view the realtime webcast?")%></span>
            <br />
            <input type="text" size="20" name="numWebcastViewers" value="" />
        </div>
    
        <!-- HOW MANY REMOTE VIEWERS -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("How many people do you expect to view the online recordings afterward?")%></span>
            <br />
            <input type="text" size="20" name="numRecordingViewers" value="" />
        </div>
    
        <!-- HOW MANY ATTENDEES -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("How many people do you expect to attend the event in person?")%></span>
            <br />
            <input type="text" size="20" name="numAttendees" value="" />
        </div>
    
    </div>
    
    <!-- DRAW BOX AROUND SECTION 3: METADATA AND SURVEY INFO -->
    <div class="WRFormSection">
        <!-- PURPOSE OF WEBCAST -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("Why do you need this event webcasted? (check all that apply)")%></span>
            <ul class="WROptionList">
                <% for value, text in WebcastPurpose: %>
                <li>
                    <input type="checkbox" name="webcastPurpose" value="<%=value%>" id="<%=value%>CB">
                    <label for="<%=value%>CB"><%=text%></label>
                </li>
                <% end %>
            </ul>
        </div>
        <!-- EXPECTED AUDIENCE -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("Who is the intended audience? (check all that apply)")%></span>
            <ul class="WROptionList">
                <% for value, text in IntendedAudience: %>
                <li>
                    <input type="checkbox" name="intendedAudience" value="<%=value%>" id="<%=value%>CB">
                    <label for="<%=value%>CB"><%=text%></label>
                </li>
                <% end %>
            </ul>
        </div>
        <!-- SUBJECT MATTER -->
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("What is the subject matter? (check all that apply)")%></span>
            <ul class="WROptionList">
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
    <div class="WRFormSection">
        <div class="WRFormSubsection">
            <span class="WRQuestion"><%=_("Please write here any other comments or instructions you may have:")%></span>
            <textarea rows="10" cols="60" name="otherComments" style="display:block;"></textarea>
        </div>
    </div>
    
    <% if IsSingleBooking: %>
    <div style="margin-top: 1em;">
        <div id="sendWebcastRequestBottom" class="sendWebcastRequestDiv" style="display:none;">
            <button onclick="send('WebcastRequest')"><%=_("Send request")%></button>
        </div>
        <div id="modifyWebcastRequestBottom" class="modifyWebcastRequestDiv" style="display:none;">
            <button onclick="send('WebcastRequest')"><%=_("Modify request")%></button>
        </div>
        <div id="withdrawWebcastRequestBottom" class="withdrawWebcastRequestDiv" style="display:none;">
            <button onclick="withdraw('WebcastRequest')"><%=_("Withdraw request")%></button>
        </div>
    </div>
    <% end %>
</div>

<% if not WebcastCapable=="true": %>
    <script type="text/javascript">
        setDisabled(document.getElementById("WRForm"));
    </script>
<% end %>
