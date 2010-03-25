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

// following added by jherr - I just copied and modified RRUpdateContributionList
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


var ButtonCreateIndicoLink = new DisabledButton(Html.input("button", {disabled:true}, $T("Create Indico Link")));
var ButtonCreateCDSRecord  = new DisabledButton(Html.input("button", {disabled:true}, $T("Create CDS Record")));

ButtonCreateCDSRecord.observeClick(function(){
    if (ButtonCreateCDSRecord.isEnabled()) {
        if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
                (RMviewMode == 'plain_video' ||
                        typeof RMselectedLOID != 'undefined' && RMselectedLOID != '')) {

            RMCreateCDSRecord();
        }
    }
});

ButtonCreateCDSRecord.observeEvent('mouseover', function(event){
    if (!ButtonCreateCDSRecord.isEnabled()) {
        tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY,
                $T("First select talk and Lecture Object"), "tooltipError");
    }
});

ButtonCreateCDSRecord.observeEvent('mouseout', function(event){
    if (!ButtonCreateCDSRecord.isEnabled()) {
        Dom.List.remove(document.body, tooltip);
    }
});

ButtonCreateIndicoLink.observeClick(function(){
    if (!ButtonCreateIndicoLink.isEnabled()) {
        if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
                (RMviewMode == 'plain_video' ||
                        typeof RMselectedLOID != 'undefined' && RMselectedLOID != '')) {

            RMCreateIndicoLink();
        }
    }
});

ButtonCreateIndicoLink.observeEvent('mouseover', function(event){
    if (!ButtonCreateIndicoLink.isEnabled()) {
        tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY,
                $T("First select talk and Lecture Object"), "tooltipError");
    }
});

ButtonCreateIndicoLink.observeEvent('mouseout', function(event){
    Dom.List.remove(document.body, tooltip);
});


IndicoUI.Effect.appear($E('RMlowerPane'), "block");

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

// jherr stuff
var RMselectedTalkId   = '';
var RMselectedLOID     = '';
var RMselectedTalkName = '';
var RMselectedLOName   = '';
var RMviewMode         = '';
var RMvideoFormat      = 'standard';

function RMbuttonModeSelect(mode) {
    RMviewMode = mode;
    if (mode == 'plain_video') {
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonNotSelected';
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonSelected';
        IndicoUI.Effect.disappear($E('RMrightPaneWebLecture'));
        IndicoUI.Effect.appear($E('RMrightPanePlainVideo'), "block");

        if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '') {
            ButtonCreateCDSRecord.enable();
            ButtonCreateIndicoLink.enable();
        }
    }
    else if (mode == 'web_lecture') {
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonNotSelected';
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonSelected';
        IndicoUI.Effect.disappear($E('RMrightPanePlainVideo'));
        IndicoUI.Effect.appear($E('RMrightPaneWebLecture'), "block");

        if (typeof RMselectedTalkId == 'undefined' || RMselectedTalkId == '' ||
            typeof RMselectedLOID == 'undefined' || RMselectedLOID == '') {
                ButtonCreateCDSRecord.disable();
                ButtonCreateIndicoLink.disable();
        }
    }
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

function RMtalkBoxOffHover(IndicoID) {
    var DivID = 'div' + IndicoID;
    if (RMselectedTalkId != IndicoID) {
        document.getElementById(DivID).className = 'RMtalkDisplay';
    }
}

function RMtalkBoxOnHover(IndicoID) {
    var DivID = 'div' + IndicoID;
    if (RMselectedTalkId != IndicoID) {
        document.getElementById(DivID).className = 'RMtalkHover';
    }
}

function RMtalkSelect(IndicoID) {
    var DivID = 'div' + IndicoID;
    // reset last selected talk div to default color before setting new background
    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '') {
        document.getElementById('div' + RMselectedTalkId).className = 'RMtalkDisplay';
    }
    RMselectedTalkId = IndicoID;
    document.getElementById('div' + RMselectedTalkId).className = 'RMtalkSelected';
    RMMatchSummaryMessage(RMselectedTalkId, RMselectedLOID);

    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLOID != 'undefined' && RMselectedLOID != '')) {
        ButtonCreateCDSRecord.enable();
        ButtonCreateIndicoLink.enable();
    }
}

function RMLOBoxOffHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLOID != DBID) {
        document.getElementById(DivID).className = 'RMLODisplay';
    }
}

function RMLOBoxOnHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLOID != DBID) {
        document.getElementById(DivID).className = 'RMLOHover';
    }
}

function RMLOSelect(DBID) {
    var DivID = 'lo' + DBID;
    // reset last selected LO div to default color before setting new background
    if (typeof RMselectedLOID != 'undefined' && RMselectedLOID != '') {
        document.getElementById('lo' + RMselectedLOID).className = 'RMLODisplay';
    }
    RMselectedLOID = DBID;
    document.getElementById('lo' + RMselectedLOID).className = 'RMLOSelected';
    RMMatchSummaryMessage(RMselectedTalkId, RMselectedLOID);

    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLOID != 'undefined' && RMselectedLOID != '')) {
        ButtonCreateCDSRecord.enable();
        ButtonCreateIndicoLink.enable();
    }
}

function RMMatchSummaryMessage(talk, LO) {
    if (typeof talk != 'undefined' &&
            talk != '' &&
            typeof LO != 'undefined' &&
            LO != '') {
        document.getElementById('RMMatchSummaryMessage').innerHTML = '<em>Match talk id</em> <b>' + talk + '</b> <em>to orphan</em> <b>' + LO + '</b>';
    }
}

function RMStatusMessage(message) {
    document.getElementById('RMStatusMessageID').innerHTML = message;
}

function RMchooseVideoFormat(format_string) {
    RMvideoFormat = format_string;

    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLOID != 'undefined' && RMselectedLOID != '')) {
        ButtonCreateCDSRecord.enable();
        ButtonCreateIndicoLink.enable();
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
                IndicoID: RMselectedTalkId,
                LOID: RMselectedLOID
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
                IndicoID: RMselectedTalkId,
                LOID: RMselectedLOID,
                videoFormat: RMvideoFormat
            },
        function(result, error){
                document.getElementById('RMMatchSummaryMessage').innerHTML = result;

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

function RMCreateIndicoLink() {

    var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating Indico link..."));

    indicoRequest('collaboration.pluginService',
            {
                plugin: 'RecordingManager',
                service: 'RMCreateIndicoLink',
                conference: '<%= ConferenceId %>',
                IndicoID: RMselectedTalkId,
                LOID: RMselectedLOID
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
