
<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Information displayed in event page</div>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-top:10px">
    <input type="checkbox" id="displayPassword" class="centeredCheckBox" name="displayPassword" value="yes"></input>
    <label for="displayPassword" class="normal">${ _("Display EVO meeting password") }</label>
    <img id="displayPasswordHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div style="margin-left:50px;padding-top:5px;">
    <input type="checkbox" id="displayPhoneBridgeId" class="centeredCheckBox" name="displayPhoneBridgeId" value="yes" checked />
    <label for="displayPhoneBridgeId" class="normal">${ _("Display phone bridge ID") }</label>
</div>

<div class="collaborationAdvancedTabCheckboxDiv">
    <input type="checkbox" id="displayPhonePassword" class="centeredCheckBox" name="displayPhonePassword" value="yes"></input>
    <label for="displayPhonePassword" class="normal">${ _("Display phone bridge password") }</label>
    <img id="displayPhonePasswordHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabCheckboxDiv">
    <input type="checkbox" id="displayPhoneBridgeNumbers" class="centeredCheckBox" name="displayPhoneBridgeNumbers" value="yes" checked />
    <label for="displayPhoneBridgeNumbers" class="normal">
        ${ _("Display link to") }
    </label>
    <a href="${ PhoneBridgeListLink }" target="_blank">
        ${ _("list of phone bridge numbers") }
    </a>
</div>

<div class="collaborationAdvancedTabCheckboxDiv" style="margin-bottom:10px">
    <input type="checkbox" id="displayURL" class="centeredCheckBox" name="displayURL" value="yes" />
    <label for="displayURL" class="normal">${ _("Display auto-join URL in event page") }</label>
    <img id="displayURLHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>

<div class="collaborationAdvancedTabTitleLine">
    <div class="collaborationAdvancedTabTitle">Other options</div>
</div>
<div style="margin-top:10px">
<%include file="/Collaboration/ConfModifCollaborationDefaultAdvancedTab.tpl"/>
</div>
