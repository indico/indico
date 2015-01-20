var RR_multiDayEvent = ${ jsBoolean(IsMultiDayEvent) };
% if ConfStartDate:
var RR_confStartDate = IndicoUtil.parseJsonDate(${ jsonEncode(ConfStartDate) });
% endif
var RR_confLocation = ${ jsonEncode(ConfLocation) }
var RR_confRoom = ${ jsonEncode(ConfRoom) }

var RRSpeakersTemplate = function(presenters) {
    var speakers = ", by "
    enumerate(presenters, function(speaker, index) {
        if (index > 0) {
            speakers += " and ";
        }
        speakers += speaker.name;
    });
    return speakers;
}

var RRTalkTemplate = function(talk) {

    // Checkbox
    var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
    checkBox.dom.value = talk.id;

    // Start date text
    var talkStartDateText;
    if (exists(talk.startDate)) {
        var startDate = IndicoUtil.parseJsonDate(talk.startDate);
        if (!RR_multiDayEvent && (startDate.getFullYear() === RR_confStartDate.getFullYear() &&
                                  startDate.getMonth() === RR_confStartDate.getMonth() &&
                                  startDate.getDate() === RR_confStartDate.getDate() )) {
            talkStartDateText = IndicoUtil.formatJustTime(startDate) + " :";
        } else {
            talkStartDateText = IndicoUtil.formatDateTime(startDate, 2) + " :";
        }
    } else {
        talkStartDateText = "(Not Scheduled) ";
    }

    var talkStartDate = Html.span("RRContributionStartDate", talkStartDateText);

    // Title
    var talkName = Html.span("RRContributionName", talk.title);

    // Duration
    var duration;
    if (exists(talk.duration)) {
        duration = Html.span("RRContributionDuration", " (" + talk.duration + ")");
    } else {
        duration = '';
    }

    // We build the label
    var label = Html.label({}, talkStartDate, talkName, duration);
    label.dom.htmlFor = "talk" + talk.id + "CB";

    // After the label, the speakers (optionally)
    if (talk.presenters.length > 0) {
        label.append(Html.span("RRSpeakers", RRSpeakersTemplate(talk.presenters)))
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

    if (contribLocation != RR_confLocation || contribRoom != RR_confRoom) {
        if (contribLocation) {
            var locationText = ' (' + contribLocation;
            if (contribRoom) {
                locationText += ', ' + contribRoom;
            }
            locationText += ')';
            label.append(Html.span("RRSpeakers", locationText));
        }
    }

    // Finally, the id
    label.append(Html.span("RRContributionId", "(id: " + talk.id + ")"));

    return Html.li({"data-recordingCapable": talk.recordingCapable}, checkBox, label);

};

var RRUpdateContributionList = function (targetId, isManager) {
    if (RR_contributions.length > 0) {
        $E(targetId).set('');
        for (i in RR_contributions) {
            contribution = RR_contributions[i];
            $E(targetId).append(RRTalkTemplate(contribution));
        }
    } else {
        if (exists($E(targetId))) { // we are not in a lecture
            $E(targetId).set(Html.span({style:{paddingLeft: pixels(20)}}, $T("This event has no talks, or none of the talks take place in a room capable of recording.")));
            // Hack to send a empty list and not make the server crash
            $E(targetId).append(Html.input('checkbox', {style:{display:"none", disabled:"disabled"},name: "talkSelection", id: "noTalks"}));
        }
    }
}

var RR_loadTalks = function (isManager) {
    var fetchContributions = function() {

        var talkTemplate = function(talk) {
            var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
            checkBox.dom.value = talk.id;
            var talkId = Html.span("RRContributionId", "[" + talk.id + "] ")
            var talkName = Html.span("RRContributionName", talk.title)
            var label = Html.label({}, talkId, talkName);
            label.dom.htmlFor = "talk" + talk.id + "CB";

            if (talk.presenters.length > 0) {
                var speakers = ", by "
                enumerate(talk.presenters, function(speaker, index) {
                    if (index > 0) {
                        speakers += " and ";
                    }
                    speakers += speaker.name;
                });
                label.append(Html.span("RRSpeakers", speakers))
            }

            if (exists(talk.location) && trim(talk.location)) {
                var locationText = ' (' + talk.location;
                if (exists(talk.room) && trim(talk.room)) {
                    locationText += ', ' + talk.room;
                }
                locationText += ')';
                label.append(Html.span("RRSpeakers", locationText))
            }
            return Html.li('', checkBox, label);
        };

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Fetching talks, may take a while..."));

        indicoRequest('collaboration.pluginService',
                {
                    plugin: 'RecordingRequest',
                    service: 'RecordingAbleTalks',
                    conference: '${ ConferenceId }'
                },
            function(result, error){
                if (!error) {
                    RR_contributions = result;
                    RRUpdateContributionList('contributionList');
                    IndicoUI.Effect.appear($E('contributionsDiv'));
                    RR_contributionsLoaded = true;
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    };

    if (RR_contributionsLoaded) {
        // Hide talks that are not capable and not choosen by managers
        if (!isManager) {
            $("#contributionList li").each(function() {
                if ($(this).attr('data-recordingCapable') == 'false') {
                    $(this).find('input').attr('disabled', 'disabled');
                    if (!$(this).find('input').is(':checked')) {
                        $(this).hide();
                    }
                }
            });
        }
        IndicoUI.Effect.appear($E('contributionsDiv'));

        //Hide list if there are no displayed talks
        if ($("#contributionList li:not(:hidden)").size() == 0) {
            RR_hideTalks();
        }

    } else {
        fetchContributions();
    }
}

var RR_hideTalks = function (){
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}

var RRSelectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        if (!checkbox.dom.disabled) {
            checkbox.dom.checked = true;
        }
    });
}

var RRUnselectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        if (!checkbox.dom.disabled) {
            checkbox.dom.checked = false;
        }
    });
}
