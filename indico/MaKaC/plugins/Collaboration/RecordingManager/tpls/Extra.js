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
                RMTalkList[RMselectedTalkId]["CDSID"] == "none" &&
                (RMviewMode == 'plain_video' ||
                        typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '')) {

            RMCreateCDSRecord();
        }
    }
    // I don't think it's possible this will ever happen...
    else {
        alert($T("You can only create a CDS record if you've selected a talk and content type, and a record doesn't already exist."));
    }
});

ButtonCreateCDSRecord.observeEvent('mouseover', function(event){
    if (!ButtonCreateCDSRecord.isEnabled()) {
        tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY,
                $T("Please select talk and content type."), "tooltipError");
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
                RMTalkList[RMselectedTalkId]["CDSID"] != "none" &&
                RMTalkList[RMselectedTalkId]["CDSID"] != "pending") {

            RMCreateIndicoLink();
        }
    }
});

ButtonCreateIndicoLink.observeEvent('mouseover', function(event){
    if (!ButtonCreateIndicoLink.isEnabled()) {
        tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY,
                $T("Please select talk and create CDS record."), "tooltipError");
    }
});

ButtonCreateIndicoLink.observeEvent('mouseout', function(event){
    Dom.List.remove(document.body, tooltip);
});

IndicoUI.Effect.appear($E('RMlowerPane'), "block");

// This function gets called when either plain_video or web_lecture buttons are clicked.
function RMbuttonModeSelect(mode) {

    // mode can either be 'plain_video' or 'web_lecture'
    RMviewMode = mode;

    if (mode == 'plain_video') {
        // effects for plain_video and web_lecture buttons
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonNotSelected';
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonSelected';
        IndicoUI.Effect.disappear($E('RMrightPaneWebLecture'));
        IndicoUI.Effect.appear($E('RMrightPanePlainVideo'), "block");

        // User has clicked on the plain_video button, so enable ButtonCreateCDSRecord
        // only if talk has already been selected and doesn't already have a CDS record.
        if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            RMTalkList[RMselectedTalkId]["CDSID"] == "none") {
            ButtonCreateCDSRecord.enable();
        }
    }
    else if (mode == 'web_lecture') {
        $E("RMbuttonPlainVideo").dom.className = 'RMbuttonNotSelected';
        $E("RMbuttonWebLecture").dom.className = 'RMbuttonSelected';
        IndicoUI.Effect.disappear($E('RMrightPanePlainVideo'));
        IndicoUI.Effect.appear($E('RMrightPaneWebLecture'), "block");

        if (typeof RMselectedTalkId == 'undefined' || RMselectedTalkId == '' ||
            typeof RMselectedLODBID == 'undefined' || RMselectedLODBID == '') {
                ButtonCreateCDSRecord.disable();
        }
    }
    else {
        // It shouldn't be possible for this function to get called without one of the 2 args
    }

    // update the summary text in the box next to the Create CDS Record button
    RMMatchSummaryMessageUpdate();
}

function RMtalkBoxOffHover(IndicoID) {
    var DivID = 'div' + IndicoID;
    if (RMselectedTalkId != IndicoID) {
        $E(DivID).dom.className = 'RMtalkDisplay';
    }
}

function RMtalkBoxOnHover(IndicoID) {
    var DivID = 'div' + IndicoID;
    if (RMselectedTalkId != IndicoID) {
        $E(DivID).dom.className = 'RMtalkHover';
    }
}

function RMtalkSelect(IndicoID) {
    var DivID = 'div' + IndicoID;
    // reset last selected talk div to default color before setting new background
    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '') {
        $E('div' + RMselectedTalkId).dom.className = 'RMtalkDisplay';
    }
    RMselectedTalkId = IndicoID;
    $E('div' + RMselectedTalkId).dom.className = 'RMtalkSelected';

    // Enable ButtonCreateCDSRecord only if RMselectedTalkId is set and either RMviewMode is plain_video or RMselectedLODBID is set,
    // AND the CDS record has not yet been created. Once you create a CDS record you can't do it again.
    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            RMTalkList[RMselectedTalkId]["CDSID"] == "none" &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '')) {
        ButtonCreateCDSRecord.enable();
    }
    else {
        ButtonCreateCDSRecord.disable();
    }

    // Enable ButtonCreateIndicoLink only if talk has been selected and CDS record already exists.
    // Other stuff like video mode and lecture object are irrelevant.
    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            RMTalkList[RMselectedTalkId]["CDSID"] != "none" &&
            RMTalkList[RMselectedTalkId]["CDSID"] != "pending" &&
            RMTalkList[RMselectedTalkId]["IndicoLink"] == 'False') {
        ButtonCreateIndicoLink.enable();
    }
    else {
        ButtonCreateIndicoLink.disable();
    }

    RMMatchSummaryMessageUpdate();
}

function RMCDSDoneOnHover(IndicoID) {
    divID = 'divCDS' + IndicoID;

    $E(divID).dom.className = 'RMcolumnStatusCDSDoneHover';

}

function RMCDSDoneOffHover(IndicoID) {
    divID = 'divCDS' + IndicoID;

    $E(divID).dom.className = 'RMcolumnStatusCDSDone';

}

function RMCDSDoneClick(url) {
    window.open(url);
}

function RMLOBoxOffHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLODBID != DBID) {
        $E(DivID).dom.className = 'RMLODisplay';
    }
}

function RMLOBoxOnHover(DBID) {
    var DivID = 'lo' + DBID;
    if (RMselectedLODBID != DBID) {
        $E(DivID).dom.className = 'RMLOHover';
    }
}

// This function is called when the user clicks on a lecture object
function RMLOSelect(DBID) {

    var DivID = 'lo' + DBID;

    // reset last selected LO div to default color before setting new background
    if (typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '') {
        $E('lo' + RMselectedLODBID).dom.className = 'RMLODisplay';
    }
    RMselectedLODBID = DBID;
    $E('lo' + RMselectedLODBID).dom.className = 'RMLOSelected';

    // If talk has been selected, and either we are in plain_video mode or LO has been selected,
    // and if the CDS record doesn't already exist, then enable Create CDS Record button
    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            RMTalkList[RMselectedTalkId]["CDSID"] == "none" &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '')) {
        ButtonCreateCDSRecord.enable();
    }

    RMMatchSummaryMessageUpdate();
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

    RMMatchSummaryMessageUpdate();
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

    RMMatchSummaryMessageUpdate();
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

    RMMatchSummaryMessageUpdate();
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

    RMMatchSummaryMessageUpdate();
}

// Populate the RMMatchSummaryMessage text box with basic info like the talk ID, LOID
function RMMatchSummaryMessageUpdate() {
    var message_list = [];

    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '') {
        message_list.push(Html.span({}, "talk: ", Html.span({style:{fontWeight: "bold"}}, RMselectedTalkId)));
    }
    if (typeof RMviewMode != 'undefined' && RMviewMode == 'plain_video') {
        if (typeof RMvideoFormat != 'undefined' && RMvideoFormat != '') {
            message_list.push(Html.span({}, ", format: ", Html.span({style:{fontWeight: "bold"}}, RMvideoFormat)));
        }
    }
    else if (typeof RMviewMode != 'undefined' && RMviewMode =='web_lecture') {
        if (typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '') {
            message_list.push(Html.span({}, ", web lecture: ", Html.span({style:{fontWeight: "bold"}}, RMLOList[RMselectedLODBID]["LOID"])));
        }
    }

    languageCodes = RMGetLanguageCodesList();

    var len = languageCodes.length;
    if (len > 0) {
        message_list.push(Html.span({}, ", languages: "))
        message_list.push(RMLanguagesString(languageCodes));
    }

    $E('RMMatchSummaryMessage').set(message_list);
}

//Build a list of language codes based on variables set
function RMGetLanguageCodesList() {

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

    return languageCodes;
}

// Build a string listing language codes
function RMLanguagesString(languageCodes) {

    var messages = [];
    var len = languageCodes.length;

    if (len > 0) {
        for(var i=0; i < len; i++) {
            languageCodes[i];
            messages.push(Html.span({style:{fontWeight: "bold"}}, languageCodes[i]))
            if (i < len - 1) {
                messages.push(Html.span({}, ", "));
            }

        }
    }

    return messages;
}

function RMStatusMessage(message) {
    $E('RMStatusMessageID').set(message);
}

function RMchooseVideoFormat(format_string) {
    RMvideoFormat = format_string;

    if (typeof RMselectedTalkId != 'undefined' && RMselectedTalkId != '' &&
            (RMviewMode == 'plain_video' ||
                    typeof RMselectedLODBID != 'undefined' && RMselectedLODBID != '')) {
        ButtonCreateCDSRecord.enable();
    }

    RMMatchSummaryMessageUpdate();
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
                LOID: RMselectedLODBID
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

// Do the AJAX thing to create the CDS record
function RMCreateCDSRecord() {

    languageCodes = RMGetLanguageCodesList();

    speakers_string = "";
    if (RMTalkList[RMselectedTalkId]["speakers"] == "") {
        speakers_string = "no speaker given";
    }
    else {
        speakers_string = RMTalkList[RMselectedTalkId]["speakers"];
    }

    // contents of popup window showing information about task before submitting plain_video record
    // CDS record creation can not be easily undone.
    if (RMviewMode == 'plain_video') {
        var confirmText = Html.div({},
                Html.span({}, $T("This will create a CDS record for the following video: ")),
                Html.br(),
                Html.br(),
                Html.span({style:{fontWeight: "bold"}}, RMTalkList[RMselectedTalkId]["title"]),
                Html.span({}, " (" + speakers_string + ")"),
                Html.br(),
                Html.br(),
                Html.span({}, $T("time scheduled") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMTalkList[RMselectedTalkId]["date_nice"]),
                Html.br(),
                Html.span({}, $T("IndicoID") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMselectedTalkId),
                Html.br(),
                Html.span({}, $T("video format") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMvideoFormat),
                Html.br(),
                Html.span({}, $T("spoken language(s)") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMLanguagesString(languageCodes)),
                Html.br(),
                Html.br(),
                Html.span({}, $T("To proceed, click OK (you will not be able to undo)."))
        );
    }
    // contents of popup window showing information about task before submitting web_lecture record
    // CDS record creation can not be easily undone.
    else if (RMviewMode =='web_lecture') {
        var confirmText = Html.div({},
                Html.span({}, $T("This will create a CDS record for the following web lecture: ")),
                Html.br(),
                Html.br(),
                Html.span({style:{fontWeight: "bold"}}, RMTalkList[RMselectedTalkId]["title"]),
                Html.span({}, " (" + speakers_string + ")"),
                Html.br(),
                Html.br(),
                Html.span({}, $T("time scheduled") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMTalkList[RMselectedTalkId]["date_nice"]),
                Html.br(),
                Html.span({}, $T("IndicoID") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMselectedTalkId),
                Html.br(),
                Html.span({}, $T("Lecture Object ID") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMLOList[RMselectedLODBID]["LOID"]),
                Html.br(),
                Html.span({}, $T("spoken language(s)") + ": "),
                Html.span({style:{fontWeight: "bold"}}, RMLanguagesString(languageCodes)),
                Html.br(),
                Html.br(),
                Html.span({}, $T("To proceed, click OK (you will not be able to undo)."))
        );
    }

    var confirmHandler = function(confirm) {

        if (confirm) {

            var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating CDS record..."));

            indicoRequest('collaboration.pluginService',
                    {
                        plugin: 'RecordingManager',
                        service: 'RMCreateCDSRecord',
                        conference: '<%= ConferenceId %>',
                        IndicoID: RMselectedTalkId,
                        LOID: RMselectedLODBID,
                        videoFormat: RMvideoFormat,
                        contentType: RMviewMode,
                        languages: languageCodes
                    },
                function(result, error){
                        $E('RMMatchSummaryMessage').set(Html.span({}, result));

                        if (!error) {

                        killProgress(); // turn off the progress indicator

                        // Reload page so you can see updated status of talks
                        window.location.reload();

                    } else {
                        killProgress(); // turn off the progress indicator
                        IndicoUtil.errorReport(error);

                    }
                }
            );



        }
    };

    var confirmPopup = new ConfirmPopup($T("Please review your choice"), confirmText, confirmHandler);
    confirmPopup.open();

}

function RMCreateIndicoLink() {

    var killProgress = IndicoUI.Dialogs.Util.progress($T("Creating Indico link..."));

    indicoRequest('collaboration.pluginService',
            {
                plugin: 'RecordingManager',
                service: 'RMCreateIndicoLink',
                conference: '<%= ConferenceId %>',
                IndicoID: RMselectedTalkId,
                LOID: RMselectedLODBID,
                CDSID: RMTalkList[RMselectedTalkId]["CDSID"]
            },
        function(result, error){
            if (!error) {
                killProgress(); // turn off the progress indicator

                // Reload page so you can see updated status of talks
                window.location.reload();


            } else {
                killProgress(); // turn off the progress indicator
                IndicoUtil.errorReport(error);
            }
        }
    );
}
