<h2 class="formTitle"><%= _("User Preferences")%></h2>
<h3>Site-wide</h3>
<table style="margin-left: 100px;">
	<tr>
	    <td class="titleCellTD"><span class="titleCellFormat"><%= _("Modification Tabs")%></span></td>
	    <td class="blacktext spaceLeft" id="tabExpandSelect"></td>
	</tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat"><%= _("Language")%></span></td>
        <td class="blacktext spaceLeft" id="selectLanguage"></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat"><%= _("My Timezone")%></span></td>
        <td class="blacktext spaceLeft" id="myTimezone"></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat"><%= _("Display Timezone")%></span></td>
        <td class="blacktext spaceLeft" id="displayTimezone"></td>
    </tr>
    <tr>
        <td class="titleCellTD"><span class="titleCellFormat"><%= _("Show past events by default")%></span></td>
        <td class="blacktext spaceLeft" id="tabShowPastEvents" style="vertical-align:middle"></td>
    </tr>
</table>


<script type="text/javascript">

	var source = jsonRpcObject(Indico.Urls.JsonRpcService, "user.personalinfo.set", {value: null});

	source.state.observe(function(state) {
           // wait for the source to be loaded
	   if (state == SourceState.Loaded) {
        	IndicoUI.Widgets.Generic.sourceSelectionField($E('tabExpandSelect'),
	   					  $C(source.accessor('tabAdvancedMode'), {
		                                     toTarget: function(value) {
			                                  return str(value);
			                             },
			                             toSource: function(value) {
			                                  return value == "true";
			                             }
			                          }),
				                 {'false': 'Basic',
					          'true': 'Advanced'});
	   }
	});

    var langCallback = function(){
        $E("selectLanguage").set(languageSelector.draw());
        languageSelector.observe(function(){
            indicoSource('user.setLanguage', {"lang":languageSelector.get()});
        });
    };
    var languageSelector = new SelectRemoteWidget("user.getLanguages",{},langCallback)

    var tzCallback = function(){
        $E("myTimezone").set(myTimezoneSelector.draw());
        myTimezoneSelector.observe(function(){
            indicoSource('user.setTimezone', {"tz":myTimezoneSelector.get()});
        });
    };
    var myTimezoneSelector = new SelectRemoteWidget("user.getTimezones",{},tzCallback);

    var displayTzCallback = function(){
        $E("displayTimezone").set(displayTimezoneSelector.draw());
        displayTimezoneSelector.observe(function(){
            indicoSource('user.setDisplayTimezone', {"tzMode":displayTimezoneSelector.get()});
        });
    };
    var displayTimezoneSelector = new SelectRemoteWidget("user.getDisplayTimezones",{},displayTzCallback);

	$E("tabShowPastEvents").set(new RemoteSwitchButton(<% if showPastEvents: %>true<% end %><% else: %>false<% end %>,
            Html.img({src:imageSrc("tick.png")}), Html.img({src:imageSrc("cross.png")}), "user.hidePastEvents", "user.showPastEvents",{}).draw());
</script>
