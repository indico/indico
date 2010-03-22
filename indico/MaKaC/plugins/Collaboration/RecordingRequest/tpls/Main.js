{
    checkParams : function () {
        return {
            "permission": ["radio", false, function(option, values){

                var errors = [];
                if (!exists(values["permission"]) || (exists(values["permission"]) && values["permission"] != "Yes")) {
                    errors.push($T("We cannot handle this request if you do not commit to ensure each speaker will give permission."));
                }
                return errors;
            }],
            "lectureOptions": ["text", true, function(option, values){
                var errors = [];
                if (option == 'chooseOne') {
                    errors.push($T("Please choose if slides and/or chalkboards will be used."));
                }
                return errors;
            }],
            "lectureStyle": ["text", true, function(option, values){
                var errors = [];
                if (option == 'chooseOne') {
                    errors.push($T("Please choose a type of event."));
                }
                return errors;
            }]
        }
    },

    errorHandler: function(event, error) {
        if (error.operation == "create") {
            CSErrorPopup($T("Could not send email to responsible"),
                         [Html.span("", $T("There was a problem when sending the notification email to the Recording responsible:"), Html.br(), error.inner)])
        }
        if (error.operation == "edit") {
            CSErrorPopup($T("Could not send email to responsible"),
                         [Html.span("", $T("There was a problem when sending the notification email to the Recording responsible:"), Html.br(), error.inner)])
        }
        if (error.operation == "remove") {
            CSErrorPopup($T("Could not send email to responsible"),
                        [Html.span("", $T("There was a problem when sending the notification email to the Recording responsible:"), Html.br(), error.inner)])
        }
    },

    customText : function(booking) {
        if (booking.acceptRejectStatus === false && trim(booking.rejectionReason)) {
            return $T("Rejection reason: ") + trim(booking.rejectionReason);
        }
    },

    clearForm : function () {
        var formNodes = IndicoUtil.findFormFields($E('RecordingRequestForm'));
        IndicoUtil.setFormValues(formNodes, {'talkSelectionComments':'', 'numRemoteViewers':'', 'numAttendees':'', 'otherComments':''});
        if (!isLecture) {
            $E('allTalksRB').dom.checked = true;
            IndicoUI.Effect.disappear($E('contributionsDiv'));
        }
        $E('permissionYesRB').dom.checked = false;
        $E('permissionNoRB').dom.checked = false;
        $E('lectureOptions').dom.value = "chooseOne";
        $E('lectureStyle').dom.value = "chooseOne";
        $E('postingUrgency').dom.value = "withinWeek";
    },

    onLoad : function() {
        RRUpdateContributionList();
        if (!isLecture) {
            if (singleBookings['RecordingRequest'] && singleBookings['RecordingRequest'].bookingParams.talks == 'choose') {
                IndicoUI.Effect.appear($E('contributionsDiv'));
            }
        }

        if(!singleBookings['RecordingRequest']) {
            callFunction('RecordingRequest','clearForm');
        }
    }
}