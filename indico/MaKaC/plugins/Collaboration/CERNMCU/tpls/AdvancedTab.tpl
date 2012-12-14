
<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Information displayed in event page</div>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="displayPin" class="centeredCheckBox" name="displayPin" value="yes"></input>
    <label for="displayPin" class="normal">${ _("Display the MCU conference's PIN") }</label>
    <img id="displayPinHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Other options</div>
</div>
<div style="margin-top:10px">
<%include file="/Collaboration/ConfModifCollaborationDefaultAdvancedTab.tpl"/>
</div>
