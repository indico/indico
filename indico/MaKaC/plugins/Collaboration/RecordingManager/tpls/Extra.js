var RR_multiDayEvent = <%= jsBoolean(IsMultiDayEvent) %>;
<% if ConfStartDate: %>
var RR_confStartDate = IndicoUtil.parseJsonDate(<%= jsonEncode(ConfStartDate) %>);
<% end %>
var RR_confLocation = <%= jsonEncode(ConfLocation) %>
var RR_confRoom = <%= jsonEncode(ConfRoom) %>

var RRSpeakersTemplate = function(speakerList) {
    var speakers = ", by "
    enumerate(speakerList, function(speaker, index) {
        if (index > 0) {
            speakers += " and ";
        }
        speakers += speaker.fullName;
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
    if (talk.speakerList.length > 0) {
        label.append(Html.span("RRSpeakers", RRSpeakersTemplate(talk.speakerList)))
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

    return Html.li('', checkBox, label);

};

// var RRUpdateContributionList = function () {
//    if (RR_contributions.length > 0) {
//$E('contributionList').set('');
//for (i in RR_contributions) {
//contribution = RR_contributions[i];
//$E('contributionList').append(RRTalkTemplate(contribution));
//}
//} else {
//$E('contributionList').set(Html.span({style:{paddingLeft: pixels(20)}}, $T("This event has no talks."))); // make this more beautiful
//}
//}

// added by jherr - I just copied and modified RRUpdateContributionList
var REUpdateOrphanList = function () {
    if (RE_orphans.length > 0) {
        $E('orphanList').set('');
        for (i in RE_orphans) {
            orphan = RE_orphans[i];
            $E('orphanList').append(RELOTemplate(orphan));
        }
    } else {
        $E('orphanList').set(Html.span({style:{paddingLeft: pixels(20)}}, $T("No orphans found.."))); // make this more beautiful
    }
}

// jherr: this is the part that loads the list of contributions
var RR_loadTalks = function () {

    var fetchContributions = function() {

        var talkTemplate = function(talk) {
            var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
            checkBox.dom.value = talk.id;
            var talkId = Html.span("RRContributionId", "[" + talk.id + "] ")
            var talkName = Html.span("RRContributionName", talk.title)
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
                    service: 'RRTalks',
                    conference: '<%= ConferenceId %>'
                },
            function(result, error){
                if (!error) {
                    RR_contributions = result;
                    RRUpdateContributionList();
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
        IndicoUI.Effect.appear($E('contributionsDiv'));

    } else {
        fetchContributions();
    }
}

var RR_hideTalks = function (){
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}

var RRSelectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        checkbox.dom.checked = true;
    });
}

var RRUnselectAllContributions = function() {
    each($N('talkSelection'), function(checkbox) {
        checkbox.dom.checked = false;
    });
}

// jherr stuff
var RMselectedTalk = '';
var RMselectedLO   = '';
var RMviewMode     = '';

function RMtoggleLectureVideo(mode) {
    RMviewMode = mode;
    if (mode == 'plain_video') {
        RMbuttonModeSelected('plain_video');
        IndicoUI.Effect.disappear($E('RMrightPaneWebLecture'));
        IndicoUI.Effect.appear($E('RMrightPanePlainVideo'), "block");
    }
    else if (mode == 'web_lecture') {
        RMbuttonModeSelected('web_lecture');
        IndicoUI.Effect.disappear($E('RMrightPanePlainVideo'));
        IndicoUI.Effect.appear($E('RMrightPaneWebLecture'), "block");
    }
    // do make the lower pane appear the first time a choice is made, and stay visible
    IndicoUI.Effect.appear($E('RMlowerPane'), "block")
}

function RMbuttonModeOnHover(mode) {
    if (mode == 'plain_video' && RMviewMode != 'plain_video') {
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonHover';
    }
    if (mode == 'web_lecture' && RMviewMode != 'web_lecture') {
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonHover';
    }
}

function RMbuttonModeOffHover(mode) {
    if (mode == 'plain_video' && RMviewMode != 'plain_video') {
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonDisplay';
    }
    if (mode == 'web_lecture' && RMviewMode != 'web_lecture') {
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonDisplay';
    }
}

function RMbuttonModeSelected(mode) {
    if (mode == 'web_lecture') {
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonDisplay';
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonSelected';
    }
    else if (mode == 'plain_video') {
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonDisplay';
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonSelected';
    }
}

function RMtalkBoxOffHover(IndicoID) {
    var DivID = 'div' + IndicoID;
    if (RMselectedTalk != IndicoID) {
        document.getElementById(DivID).className = 'RMtalkDisplay';
    }
}

function RMtalkBoxOnHover(IndicoID) {
    var DivID = 'div' + IndicoID;
//    alert('selected: ' + RMselectedTalk + ' DivID: ' + DivID)
    if (RMselectedTalk != IndicoID) {
        document.getElementById(DivID).className = 'RMtalkHover';
    }
}

function RMtalkSelect(IndicoID) {
    var DivID = 'div' + IndicoID;
    // first reset last selected talk div to default color
    if (RMselectedTalk != '') {
        document.getElementById('div' + RMselectedTalk).className = 'RMtalkDisplay';
    }
    RMselectedTalk = IndicoID;
    document.getElementById('div' + RMselectedTalk).className = 'RMtalkSelected';
    RMStatusMessage(RMselectedTalk, RMselectedLO)
}

function RMLOBoxOffHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLO != DBID) {
        document.getElementById(DivID).className = 'RMLODisplay';
    }
}

function RMLOBoxOnHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLO != DBID) {
        document.getElementById(DivID).className = 'RMLOHover';
    }
}

function RMLOSelect(DBID) {
    var DivID = 'lo' + DBID;
    // reset last selected LO div to default color before setting new background
    if (RMselectedLO != '') {
        document.getElementById('lo' + RMselectedLO).className = 'RMLODisplay';
    }
    RMselectedLO = DBID;
    document.getElementById('lo' + RMselectedLO).className = 'RMLOSelected';
    RMStatusMessage(RMselectedTalk, RMselectedLO)
}

function RMStatusMessage(talk, LO) {
    document.getElementById('RMStatusMessageID').innerHTML = 'To export metadata from talk id ' + talk + ' to the orphan lecture ' + LO + ' ';
}

function RMchooseVideoFormat(format_string) {
    if (format_string == '4/3') {

    }
    else if (format_string == '16/9') {

    }

}

function RMLink() {
    //RMselectedTalk
    //RMselectedLO

    var killProgress = IndicoUI.Dialogs.Util.progress($T("doing something"));

    indicoRequest('collaboration.pluginService',
            {
                plugin: 'RecordingManager',
                service: 'RMLink',
                conference: '<%= ConferenceId %>',
                IndicoID: RMselectedTalk,
                LOID: RMselectedLO
            },
        function(result, error){
            if (!error) {
// I don't have anything here yet. This is where we could do something with the result if we want. Don't know what that would be.
                killProgress(); // turn off the progress indicator
            } else {
                killProgress(); // turn off the progress indicator
                IndicoUtil.errorReport(error);
            }
        }
    );
}

function RMCreateCDSRecord() {

    var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating CDS record..."));

    indicoRequest('collaboration.pluginService',
            {
                plugin: 'RecordingManager',
                service: 'RMCreateCDSRecord',
                conference: '<%= ConferenceId %>',
                IndicoID: RMselectedTalk,
                LOID: RMselectedLO
            },
        function(result, error){
            if (!error) {
// I don't have anything here yet. This is where we could do something with the result if we want. Don't know what that would be.
                killProgress(); // turn off the progress indicator

            } else {
                killProgress(); // turn off the progress indicator
                IndicoUtil.errorReport(error);
            }
        }
    );
}
