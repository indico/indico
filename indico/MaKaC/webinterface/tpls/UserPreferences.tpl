<h2 class="formTitle">${ _("User Preferences")}</h2>
<table style="margin-left: 100px;">
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Language")}</span></td>
        <td class="blacktext spaceLeft"><div id="selectLanguage" class="userPrefOption"></div><div id="langStatus" class="userPrefOptionStatus"></div></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("My Timezone")}</span></td>
        <td class="blacktext spaceLeft"><div id="myTimezone" class="userPrefOption"></div><div id="myTimezoneStatus" class="userPrefOptionStatus"></div></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat">${ _("Display Timezone")}</span></td>
        <td class="blacktext spaceLeft"><div id="displayTimezone" class="userPrefOption"></div><div id="displayTimezoneStatus" class="userPrefOptionStatus"></div></td>
    </tr>
    <tr>
        <td class="titleCellTD" nowrap><span class="titleCellFormat">${ _("Show past events by default")}</span></td>
        <td class="blacktext spaceLeft" nowrap><div id="tabShowPastEvents"></div></td>
    </tr>
    % if pluginUserPreferences:
        ${pluginUserPreferences}
    % endif
</table>

<script type="text/javascript">

    var checkState = function(statusId) {
        var status = $E(statusId);
        status.dom.style.color = "orange";
        status.set("Saving...");
        var _checkState = function(state){
            if (state == SourceState.Error) {
                IndicoUtil.errorReport($T("Error saving"));
                status.set("");
            } else if (state == SourceState.Loaded) {
                status.dom.style.color = "green";
                status.set("Saved!");
                setTimeout(function(){
                    status.set("");
                }, 1000);
            }
    };
    return _checkState;
    };

    var langCallback = function(){
        $E("selectLanguage").set(languageSelector.draw());
        languageSelector.observe(function(){
            var req = indicoSource('user.setLanguage', {"userId": "${userId}", "lang":languageSelector.get()});
            req.state.observe(checkState("langStatus"));
        });
    };
    var languageSelector = new SelectRemoteWidget("user.getLanguages",{"userId": "${userId}"},langCallback, null, null, ${defaultLanguage | h, j});

    var tzCallback = function(){
        $E("myTimezone").set(myTimezoneSelector.draw());
        myTimezoneSelector.observe(function(){
            var req = indicoSource('user.setTimezone', {"userId": "${userId}", "tz":myTimezoneSelector.get()});
            req.state.observe(checkState("myTimezoneStatus"));
        });
    };
    var myTimezoneSelector = new SelectRemoteWidget("user.getTimezones",{"userId": "${userId}"},tzCallback, null, null, ${defaultTimezone | h, j});

    var displayTzCallback = function(){
        $E("displayTimezone").set(displayTimezoneSelector.draw());
        displayTimezoneSelector.observe(function(){
            var req = indicoSource('user.setDisplayTimezone', {"userId": "${userId}", "tzMode":displayTimezoneSelector.get()});
            req.state.observe(checkState("displayTimezoneStatus"));
        });
    };
    var displayTimezoneSelector = new SelectRemoteWidget("user.getDisplayTimezones",{"userId": "${userId}"},displayTzCallback, null, null, ${defaultDisplayTimeZone | h, j});

    $E("tabShowPastEvents").set(new RemoteSwitchButton(${"true" if showPastEvents else "false"},
            Html.img({src:imageSrc("tick.png")}), Html.img({src:imageSrc("cross.png")}), "user.hidePastEvents", "user.showPastEvents",{"userId": "${userId}"}).draw());
</script>
