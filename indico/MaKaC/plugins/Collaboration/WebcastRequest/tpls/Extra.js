var WR_multiDayEvent = <%= jsBoolean(IsMultiDayEvent) %>;
<% if ConfStartDate: %>
var WR_confStartDate = IndicoUtil.parseJsonDate(<%= jsonEncode(ConfStartDate) %>);
<% end %>
var WR_confLocation = <%= jsonEncode(ConfLocation) %>
var WR_confRoom = <%= jsonEncode(ConfRoom) %>


var WRSpeakersTemplate = function(speakerList) {
    var speakers = ", by "
    enumerate(speakerList, function(speaker, index) {
        if (index > 0) {
            speakers += " and ";
        }
        speakers += speaker.fullName;
    });
    return speakers;
}

var WRTalkTemplate = function(talk) {

    // Checkbox
    var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
    checkBox.dom.value = talk.id;

    // Start date text
    var talkStartDateText;
    if (exists(talk.startDate)) {
        var startDate = IndicoUtil.parseJsonDate(talk.startDate);
        if (!WR_multiDayEvent && (startDate.getFullYear() === WR_confStartDate.getFullYear() &&
                                  startDate.getMonth() === WR_confStartDate.getMonth() &&
                                  startDate.getDate() === WR_confStartDate.getDate() )) {
            talkStartDateText = IndicoUtil.formatJustTime(startDate) + " :";
        } else {
            talkStartDateText = IndicoUtil.formatDateTime(startDate, 2) + " :";
        }
    } else {
        talkStartDateText = "(Not Scheduled) ";
    }

    var talkStartDate = Html.span("WRContributionStartDate", talkStartDateText);

    // Title
    var talkName = Html.span("WRContributionName", talk.title);

    // Duration
    var duration;
    if (exists(talk.duration)) {
        duration = Html.span("WRContributionDuration", " (" + talk.duration + ")");
    } else {
        duration = '';
    }

    // We build the label
    var label = Html.label({}, talkStartDate, talkName, duration);
    label.dom.htmlFor = "talk" + talk.id + "CB";

    // After the label, the speakers (optionally)
    if (talk.speakerList.length > 0) {
        label.append(Html.span("WRSpeakers", WRSpeakersTemplate(talk.speakerList)))
    }

    // And after the speakers, the location and room (optionally)
    var contribLocation = "";
    var contribRoom = ""
    if (exists(talk.location) && trim(talk.location)) {
        contribLocation = trim(talk.location);
    }
    if (exists(talk.room) && trim(talk.room)) {
        contribRoom = trim(talk.room);
    }

    if (contribLocation != WR_confLocation || contribRoom != WR_confRoom) {
        if (contribLocation) {
            var locationText = ' (' + contribLocation;
            if (contribRoom) {
                locationText += ', ' + contribRoom;
            }
            locationText += ')';
            label.append(Html.span("WRSpeakers", locationText));
        }
    }

    // Finally, the id
    label.append(Html.span("WRContributionId", "(id: " + talk.id + ")"));

    return Html.li('', checkBox, label);

};

var WRUpdateContributionList = function () {
    if (WR_contributions.length > 0) {
        $E('contributionList').set('');
        for (i in WR_contributions) {
            contribution = WR_contributions[i];
            $E('contributionList').append(WRTalkTemplate(contribution));
        }
    } else {
        if (exists($E('contributionList'))) { // we are not in a lecture
            $E('contributionList').set(Html.span({style:{paddingLeft: pixels(20)}}, $T("This event has no talks, or none of the talks take place in a room capable of webcasting.")));
        }
    }
}

var WR_loadTalks = function () {

    var fetchContributions = function() {

        var talkTemplate = function(talk) {
            var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
            checkBox.dom.value = talk.id;
            var talkId = Html.span("WRContributionId", "[" + talk.id + "] ")
            var talkName = Html.span("WRContributionName", talk.title)
            var label = Html.label({}, talkId, talkName);
            label.dom.htmlFor = "talk" + talk.id + "CB";

            if (talk.speakerList.length > 0) {
                var speakers = ", by "
                enumerate(talk.speakerList, function(speaker, index) {
                    if (index > 0) {
                        speakers += " and ";
                    }
                    speakers += speaker.fullName;
                });
                label.append(Html.span("WRSpeakers", speakers))
            }

            if (exists(talk.location) && trim(talk.location)) {
                var locationText = ' (' + talk.location;
                if (exists(talk.room) && trim(talk.room)) {
                    locationText += ', ' + talk.room;
                }
                locationText += ')';
                label.append(Html.span("WRSpeakers", locationText))
            }

            var li = Html.li();
            li.append(checkBox);
            li.append(label);
            return li;
        };

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Fetching talks, may take a while..."));
        indicoRequest('collaboration.pluginService',
            {
                plugin: 'WebcastRequest',
                service: 'WebcastAbleTalks',
                conference: '<%= ConferenceId %>'
            },
            function(result, error){
                if (!error) {
                    WR_contributions = result;
                    WRUpdateContributionList();
                    IndicoUI.Effect.appear($E('contributionsDiv'));
                    WR_contributionsLoaded = true;
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    };

    if (WR_contributionsLoaded) {
        IndicoUI.Effect.appear($E('contributionsDiv'));
    } else {
        fetchContributions();
    }

}


var WR_hideTalks = function () {
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}


var WRSelectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        checkbox.dom.checked = true;
    });
}
var WRUnselectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        checkbox.dom.checked = false;
    });
}
