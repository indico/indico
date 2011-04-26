% if CanBeNotified:
<!-- // If this booking in particular cannot be notified of date changes any more, we disable the checkbox -->
<div class="collaborationAdvancedTabCheckboxDiv">
    <input type="checkbox" id="dateSyncCheckBox" class="centeredCheckBox" name="notifyOnDateChanges" value="yes" checked />
    <label for="dateSyncCheckBox" class="normal">${ _("Keep booking synchronized with event") }</label>
    <img id="dateSyncHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>
% endif

<div class="collaborationAdvancedTabCheckboxDiv">
    <input type="checkbox" id="hiddenCheckBox" class="centeredCheckBox" name="hidden" value="yes"></input>
    <label for="hiddenCheckBox" class="normal">${ _("Keep this booking hidden") }</label>
    <img id="hiddenHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
</div>
