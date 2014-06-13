
<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Information displayed in event page</div>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="displayPin" class="centeredCheckBox" name="displayPin" value="yes"></input>
    <label for="displayPin" class="normal">${ _("Display the Public room's PIN") }</label>
    <img id="displayPinHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="displayURL" class="centeredCheckBox" name="displayURL" value="yes" checked="checked" />
    <label for="displayURL" class="normal">${ _("Display auto-join URL in event page") }</label>
    <img id="displayURLHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-bottom:10px">
    <input type="checkbox" id="displayPhoneNumbers" class="centeredCheckBox" name="displayPhoneNumbers" value="yes" checked="checked" />
    <label for="displayPhoneNumbers" class="normal">${ _("Display phone access numbers in event page") }</label>
</div>

<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Other options</div>
</div>
<div style="margin-top:10px">
<%include file="/Collaboration/ConfModifCollaborationDefaultAdvancedTab.tpl"/>
</div>
