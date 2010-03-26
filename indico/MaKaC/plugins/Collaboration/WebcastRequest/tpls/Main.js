{
    checkParams : function () {
        return {
            "permission": ["radio", false, function(option, values){
                var errors = [];
                if (!exists(values["permission"])) {
                    errors.push($T("Please answer if all the speakers given permission to have their talks webcasted."));
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
                         [Html.span("", $T("There was a problem when sending the notification email to the Webcast responsible:"), Html.br(), error.inner)])
        }
        if (error.operation == "edit") {
            CSErrorPopup($T("Could not send email to responsible"),
                         [Html.span("", $T("There was a problem when sending the notification email to the Webcast responsible:"), Html.br(), error.inner)])
        }
        if (error.operation == "remove") {
            CSErrorPopup($T("Could not send email to responsible"),
                        [Html.span("", $T("There was a problem when sending the notification email to the Webcast responsible:"), Html.br(), error.inner)])
        }
    },

    customText : function(booking) {
        if (booking.acceptRejectStatus === false && trim(booking.rejectReason)) {
            return $T("Rejection reason: ") + trim(booking.rejectReason);
        }
    },

    clearForm : function () {
        var formNodes = IndicoUtil.findFormFields($E('WebcastRequestForm'));
        IndicoUtil.setFormValues(formNodes, {'talkSelectionComments':'', 'numWebcastViewers':'','numRecordingViewers':'', 'numAttendees':'', 'otherComments':''})
        if (!isLecture) {
            $E('allTalksRB').dom.checked = true;
            IndicoUI.Effect.disappear($E('contributionsDiv'));
        }

        $E('permissionYesRB').dom.checked = false;
        $E('permissionNoRB').dom.checked = false;
        $E('lectureOptions').dom.value = "chooseOne";
        $E('lectureStyle').dom.value = "chooseOne";
        $E('postingUrgency').dom.value = "never";
    },

    onLoad : function() {

        WRUpdateContributionList();

        IndicoUtil.enableDisableForm($E("WRForm"), WRWebcastCapable);

        if (!isLecture) {
            if (singleBookings['WebcastRequest'] && singleBookings['WebcastRequest'].bookingParams.talks == 'choose') {
                IndicoUI.Effect.appear($E('contributionsDiv'));
            }
        }

        if(!singleBookings['WebcastRequest']) {
            callFunction('WebcastRequest', 'clearForm');
        }
    }
}