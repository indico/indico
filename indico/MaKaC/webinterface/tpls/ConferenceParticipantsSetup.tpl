<table>
<tr>
   <td nowrap colspan="10">
        <div class="CRLgroupTitleNoBorder">${ _("Participation setup") }
        </div>
    </td>
</tr>
<tr>
    <td style="padding-right:15px">${ _(" When a participant is added, an email notification will be sent to him")}</td>
    <td>
        <div id="inPlaceEditAddedInfo"></div>
    </td>
</tr>

<tr>
    <td style="padding-right:15px">${ _("The list of participants is displayed on the event page")}</td>
    <td class="blacktext">
        <div id="inPlaceEditDisplay"></div>
    </td>
</tr>
<tr>
    <td style="padding-right:15px">${ _("Users may apply to participate in this event")}</td>
    <td class="blacktext">
        <div id="inPlaceEditAllowForApply"></div>
    </td>
</tr>
<tr>
    <td style="padding-right:15px">${ _("Participation requests must be approved by the event managers (you)")}</td>
    <td class="blacktext">
        <div id="inPlaceEditAutoAccept"></div>
    </td>
</tr>

<tr id="notifyMgrNewParticipant">
    <td style="padding-right:15px">${ _("Notify the managers by email when a new participant applies")}</td>
    <td class="blacktext">
        <div id="inPlaceEditNotifyMgrNewParticipant" style="display:inline;"></div>
    </td>
</tr>

<tr>
    <td style="padding-right:15px">${ _("Maximum number of participants (0 means unlimited)")}</td>
    <td class="blacktext">
        <div id="inPlaceEditNumMaxParticipants" style="display:inline;"></div>
    </td>
</tr>
</table>

<script type="text/javascript">

function reloadOptions(response, error) {
    if (!exists(error)) {
        if (!response) {
            $("#notifyMgrNewParticipant").hide();
        } else {
            if(!$('#notifyMgrNewParticipant').is(':visible')) {
                $("#notifyMgrNewParticipant").show();
                $("#notifyMgrNewParticipant").effect("highlight", {}, 3000);
            }
        }
    }
}

IndicoUI.executeOnLoad(function(){
    $("#inPlaceEditAddedInfo").append($(new RemoteSwitchButton(${"true" if addedInfo else "false"},
            Html.img({src:imageSrc("enabledSection.png")}), Html.img({src:imageSrc("disabledSection.png")}), "event.participation.addedInfo", "event.participation.addedInfo",{confId:${confId}}).draw().dom));
    $("#inPlaceEditDisplay").append($(new RemoteSwitchButton(${"true" if allowDisplay else "false"},
            Html.img({src:imageSrc("enabledSection.png")}), Html.img({src:imageSrc("disabledSection.png")}), "event.participation.allowDisplay", "event.participation.allowDisplay",{confId:${confId}}).draw().dom));
    $("#inPlaceEditAllowForApply").append($(new RemoteSwitchButton(${"true" if allowForApply else "false"},
            Html.img({src:imageSrc("enabledSection.png")}), Html.img({src:imageSrc("disabledSection.png")}), "event.participation.allowForApply", "event.participation.allowForApply",{confId:${confId}}).draw().dom));
    $("#inPlaceEditAutoAccept").append($(new RemoteSwitchButton(${"false" if autoAccept else "true"},
            Html.img({src:imageSrc("enabledSection.png")}), Html.img({src:imageSrc("disabledSection.png")}), "event.participation.autoAccept", "event.participation.autoAccept",{confId:${confId}}, reloadOptions).draw().dom));
    $("#inPlaceEditNotifyMgrNewParticipant").append($(new RemoteSwitchButton(${"true" if notifyMgrNewParticipant else "false"},
            Html.img({src:imageSrc("enabledSection.png")}), Html.img({src:imageSrc("disabledSection.png")}), "event.participation.notifyMgrNewParticipant", "event.participation.notifyMgrNewParticipant",{confId:${confId}}).draw().dom));
    $("#inPlaceEditNumMaxParticipants").append(new InputEditWidget('event.participation.setNumMaxParticipants',
            {confId:${confId}}, ${ jsonEncode(numMaxParticipants) }, false, null, function(value){return IndicoUtil.isInteger(value);}, $T("The value set is not a positive number"), $T("Please insert a positive number or 0 for unlimited"),
            null).draw().dom);

    reloadOptions(${autoAccept | n,j});
   });
</script>
