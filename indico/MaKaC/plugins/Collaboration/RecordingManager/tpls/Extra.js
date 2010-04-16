var ButtonCreateIndicoLink = new DisabledButton(Html.input("button", {disabled:true}, $T("Create Indico Link")));
var ButtonCreateCDSRecord  = new DisabledButton(Html.input("button", {disabled:true}, $T("Create CDS Record")));

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
    if (ButtonCreateIndicoLink.isEnabled()) {
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

function RMCDSDoneOnHover(IndicoID) {
    divID = 'divCDS' + IndicoID;

    document.getElementById(divID).className = 'RMcolumnStatusCDSDoneHover';

}

function RMCDSDoneOffHover(IndicoID) {
    divID = 'divCDS' + IndicoID;

    document.getElementById(divID).className = 'RMcolumnStatusCDSDone';

}

function RMCDSDoneClick(url) {
    window.location = url;
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

//Set RMLanguageFlagPrimary to true/false depending on whether box is checked
//Also set RMLanguageValuePrimary equal to the language code
function RMLanguageTogglePrimary(language) {
    if ($E('RMLanguagePrimary').dom.checked == true) {
        RMLanguageFlagPrimary  = true;
        RMLanguageValuePrimary = language;
    }
    else {
        RMLanguageFlagPrimary = false;
    }
}

// Set RMLanguageFlagSecondary to true/false depending on whether box is checked
// Also set RMLanguageValueSecondary equal to the language code
function RMLanguageToggleSecondary(language) {
    if ($E('RMLanguageSecondary').dom.checked == true) {
        RMLanguageFlagSecondary  = true;
        RMLanguageValueSecondary = language;
    }
    else {
        RMLanguageFlagSecondary = false;
    }
}

// Set RMLanguageFlagOther to true/false depending on whether box is checked
// If box is unchecked, also reset the drop-down list
function RMLanguageToggleOther() {
    if ($E('RMLanguageOther').dom.checked == true) {
        RMLanguageFlagOther = true;
    }
    else {
        RMLanguageFlagOther = false;
        $E('RMLanguageOtherSelect').dom.selectedIndex = 0;
    }

}

// If drop-down list is clicked, either it was reset to index = 0, in which case uncheck the Other box,
// or a language was selected, in which case set RMLanguageValueOther appropriately and check the Other box
function RMLanguageSelectOther(language) {
    if ($E('RMLanguageOtherSelect').dom.selectedIndex == 0) {
        $E('RMLanguageOther').dom.checked = false;
        RMLanguageFlagOther = false;
    }
    else {
        $E('RMLanguageOther').dom.checked = true;
        RMLanguageFlagOther = true;
        RMLanguageValueOther = language;
    }
}

//
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

    languageCodes = [];
    if (RMLanguageFlagPrimary == true) {
        languageCodes.push(RMLanguageValuePrimary);
    }
    if (RMLanguageFlagSecondary == true) {
        languageCodes.push(RMLanguageValueSecondary);
    }
    if (RMLanguageFlagOther == true) {
        languageCodes.push(RMLanguageValueOther);
    }

    indicoRequest('collaboration.pluginService',
            {
                plugin: 'RecordingManager',
                service: 'RMCreateCDSRecord',
                conference: '<%= ConferenceId %>',
                IndicoID: RMselectedTalkId,
                LOID: RMselectedLOID,
                videoFormat: RMvideoFormat,
                contentType: RMviewMode,
                languages: languageCodes
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
                LOID: RMselectedLOID,
                CDSID: RMTalkList[RMselectedTalkId]
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
