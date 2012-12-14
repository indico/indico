
<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">${ _("Information displayed in event page")}</div>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="showAccessPassword" class="centeredCheckBox" name="showAccessPassword" value="yes" ></input>
    <label for="showAccessPassword" class="normal">${ _("Show access password on event display page?")}</label>
    <img id="showAccessPasswordHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">${ _("WebEx advanced options")}</div>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="seeParticipants" class="centeredCheckBox" name="seeParticipants" value="yes" checked></input>
    <label for="seeParticipants" class="normal">${ _("Enable attendees to see list of participants?")}</label>
    <img id="seeParticipantsHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
    <br/>

    <input type="checkbox" id="enableChat" class="centeredCheckBox" name="enableChat" value="yes" checked></input>
    <label for="enableChat" class="normal">${ _("Enable private text chat between attendees?")}</label>
    <img id="enableChatHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
    <br/>

    <input type="checkbox" id="joinBeforeHost" class="centeredCheckBox" name="joinBeforeHost" value="yes" checked></input>
    <label for="joinBeforeHost" class="normal">${ _("Attendees can join before host?")}</label>
    <img id="joinBeforeHostHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
    <br/>

    <label for="joinBeforeTime" class="normal">${ _("Time attendees can join before event start time (in minutes)?")}</label>
    <img id="joinBeforeTimeHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" /><br/>
    <input type="radio" class="centeredCheckBox" name="joinBeforeTime" value="0" />0
    <input type="radio" class="centeredCheckBox" name="joinBeforeTime" value="300" />5
    <input type="radio" class="centeredCheckBox" name="joinBeforeTime" value="600" />10
    <input type="radio" class="centeredCheckBox" name="joinBeforeTime" value="900" checked />15
</div>


<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">${ _("Other options")}</div>
</div>
<div style="margin-top:10px">
<%include file="/Collaboration/ConfModifCollaborationDefaultAdvancedTab.tpl"/>
</div>
