{
    start : function(booking, iframeElement) {
            var popup = new WebExLaunchClientPopup(booking.startURL);
            popup.open();
    },

    checkStart : function(booking) {
        booking.permissionToStart = true;
        return true;
    },

    checkParams: function() {
        return {
            'meetingTitle' : ['text', false],
            'webExPass' : ['text', false],
            'webExUser' : ['text', false],
            'startDate' : ['datetime', false, function(startDateString, values){
                var errors = [];
                var startDate = IndicoUtil.parseDateTime(startDateString);

                var startDatePlusExtraTime = new Date();
                startDatePlusExtraTime.setTime(startDate.getTime() + ${ AllowedStartMinutes } *60*1000);
                if (beforeNow(startDatePlusExtraTime)) {
                    errors.push($T("Start date cannot be before the past ${ AllowedStartMinutes } minutes"));
                }

                // check start date is not before the minimum start date (event start date - ${ AllowedMarginMinutes } min )
                if (startDate < IndicoUtil.parseDateTime("${ MinStartDate }")) {
                    errors.push($T("Start date more than ${ AllowedMarginMinutes } minutes before event"));
                }

                // check start date is not after the maximum start date (event end date + ${ AllowedMarginMinutes } min )
                if (startDate > IndicoUtil.parseDateTime("${ MaxEndDate }")) {
                    errors.push($T("Start date more than ${ AllowedMarginMinutes } minutes after event"));
                }

                // check start date is not after end date, if end date exists
                var endDate = IndicoUtil.parseDateTime(values["endDate"]);
                if (endDate) {
                    if (startDate > endDate) {
                        errors.push($T("End date cannot be before start date."));
                    }
                }

                return errors;
            }],

            'endDate' : ['datetime', false, function(endDateString, values){
                var errors = [];
                var endDate = IndicoUtil.parseDateTime(endDateString);

                //check end date is not in the past
                if (beforeNow(endDate)) {
                    errors.push($T("End date cannot be before the current time"));
                }

                // check end date is not after the maximum start date (event end date + ${ AllowedMarginMinutes } min )
                if (endDate > IndicoUtil.parseDateTime("${ MaxEndDate }")) {
                    errors.push($T("End date more than ${ AllowedMarginMinutes } minutes after event"));
                }

                // check start date is not before the minimum start date (event start date - ${ AllowedMarginMinutes } min )
                if (endDate < IndicoUtil.parseDateTime("${ MinStartDate }")) {
                    errors.push($T("End date more than ${ AllowedMarginMinutes } minutes before the event"));
                }

                // check start date is not after end date, if start date exists
                var startDate = IndicoUtil.parseDateTime(values["startDate"]);
                if (startDate) {
                    if (startDate > endDate) {
                        errors.push($T("End date cannot be before start date."));
                    }
                }
                return errors;
            }]
        }
    },

    errorHandler: function(event, error) {
        if (event == 'create' || event == 'edit' || event == 'checkStatus') {
            if (error.faultCode == 'webex_expired_user' || error.faultCode == 'webex_invalid_user') {
                var message = $T('The specified WebEx user ID has either expired or is inactive.');
                CSErrorPopup($T("WebEx User Error"), [error.info]);
                IndicoUtil.markInvalidField($E('webExUser'), "Please provide a valid host user ID");
            }
            else if (error.faultCode == 'webex_invalid_pass') {
                CSErrorPopup($T("WebEx Password Error"), [error.info]);
                IndicoUtil.markInvalidField($E('webExPass'), "Please provide the correct password.");
            }
            else if (error.faultCode == 'webex_date_error' || error.faultCode == 'webex_duration_error') {
                CSErrorPopup($T("WebEx Date Error"), [error.info]);
                IndicoUtil.markInvalidField($E('startDate'), "WebEx has rejected the date");
                IndicoUtil.markInvalidField($E('endDate'), "WebEx has rejected the date");
            }
            else if (error.faultCode == 'webex_invalid_pass_characters') {
                CSErrorPopup($T("Invalid Meeting Password"), [error.info]);
            }
            else if (error.faultCode == 'webex_record_not_found') {
                var message = $T('WebEx could not find a record with this meeting key.');
                CSErrorPopup($T("Meeting not found"), [error.info]);
            }
            else {  //if (error.faultCode == 'webex_unknown'){
                var text = [error.info];
                text[0].replace("&quot;", '"');
                text[0].replace("&amp;", '&');
                text[0].replace("&lt;", '<');
                text[0].replace("&gt;", '>');
                CSErrorPopup($T("WebEx Error"), text);
            }
        }

        if (event == 'remove') {
            if (error.faultCode == 'cannotDeleteOld') {
                CSErrorPopup($T("Cannot remove"), [$T("It is not possible to delete an old WebEx meeting")]);
            }
            else if (error.faultCode == 'cannotDeleteOngoing') {
                CSErrorPopup($T("Cannot remove"), [$T("It is not possible to delete an ongoing WebEx meeting")]);
            }
            else if (error.faultCode == 'cannotDeleteNonExistant') {
                CSErrorPopup($T("Cannot remove"), [$T("It seems that WebEx meeting was already deleted by another party")]);
            }
            else
                CSErrorPopup($T("Error during delete"), [$T(error.info)]);
        }
    },

    customText: function(booking) {
        if (booking.error && booking.errorMessage) {
            return '<span class="collaborationWarning">' + booking.errorMessage + '<\/span>'
        } else {
            return booking.bookingParams.startDate.substring(11) + " to " + booking.bookingParams.endDate.substring(11);
        }
    },

    showInfo : function(booking) {
        infoHTML = '<div><table><tbody>';

        if (booking.error && booking.errorDetails) {
            infoHTML +=
            '<tr><td colspan="2">'+
                '<span class="collaborationWarning">';
                    booking.errorDetails +
                '<\/span>' +
            '<\/td><\/tr>'
        }

        if (booking.changesFromWebEx.length > 0) {
            infoHTML +=
            '<tr><td colspan="2">'+
                '<div class="collaborationWarning" style="display: inline;">' +
                    $T('Changes to WebEx event:') +
                    '<ul>'

            for (var i=0; i<booking.changesFromWebEx.length; i++) {
                infoHTML +=
                        '<li>' +
                            booking.changesFromWebEx[i] +
                        '<\/li>'
            }

            infoHTML +=
                    '<\/ul>' +
                '<\/div>' +
            '<\/td><\/tr>'
        }

        infoHTML +=
            '<tr><td class="collaborationInfoLeftCol">' + $T('Meeting title:') + '<\/td><td>' +
                booking.bookingParams.meetingTitle +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Start date:') + '<\/td><td>' +
                formatDateStringCS(booking.bookingParams.startDate) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('End date:') + '<\/td><td>' +
                formatDateStringCS(booking.bookingParams.endDate) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Meeting description:') + '<\/td><td>' +
                booking.bookingParams.meetingDescription +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Access password:') + '<\/td><td>' +
                (booking.bookingParams.hasAccessPassword? $T("Access password hidden") : $T("No access password was defined")) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Visibility') + '<\/td><td>' +
                (booking.bookingParams.hidden? $T("Hidden") : $T("Visible")) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Auto-join URL:') + '<\/td><td>' +
                (booking.url? '<a href="' + booking.url + '" target="_blank">' + booking.url + '</a>' : $T("not assigned yet")) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Indico booking ID:') + '<\/td><td>' +
                booking.id +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('WebEx ID:') + '<\/td><td>' +
                booking.webExKey +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('WebEx Creator Username:') + '<\/td><td>' +
                booking.webExUser +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Booking created on:') + '<\/td><td>' +
                formatDateTimeCS(booking.creationDate) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Booking last modified on:') + '<\/td><td>' +
                formatDateTimeCS(booking.modificationDate) +
            '<\/td><\/tr>'+

        '<\/tbody><\/table><\/div>'

        return infoHTML;
    },

    getDateFields : function() {
        document.getElementById('loggedInEmail').value = "${ LoggedInEmail }";
        return ["startDate", "endDate"]
    },

    onCreate: function() {
        pf = new WebExParticipantListField();
        $E('participantsCell').set(pf.draw());
        WebExDrawContextHelpIcons();
    },

    onEdit: function(booking) {
        pf = new WebExParticipantListField(booking.bookingParams.participants)
        $E('participantsCell').set(pf.draw());
        WebExDrawContextHelpIcons();
    },

    onSave: function(values) {
        var participants = pf.getParticipants();
        values["participants"] = participants;

        var ips = {}
        var errors = false;
        for (var i = 0; i < participants.length.get(); i++) {
            var participant = participants.item(i).get();
            if ( !( /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test( participant.get("email") )) )
            {
                CSErrorPopup("Invalid participants", ["The participant " + (i + 1) + " has an invalid email address"]);
                errors = true;
            }

        }

        return !errors;
    },

    postCreate: function(booking) {
        if (booking.warning) {
            var popup = new AlertPopup("Booking creation message", Html.span({},booking.warning, Html.br(), booking.message ));
                popup.open();
        }
    },

    postEdit: function(booking) {
        if (booking.warning) {
            var popup = new AlertPopup("Booking modification message", Html.span({},booking.warning, Html.br(), booking.message ));
                popup.open();
        }
    },

    postDelete: function(booking) {
        if (booking.warning) {
            var popup = new AlertPopup("Booking deletion message", Html.span({},booking.warning, Html.br(), booking.message ));
                popup.open();
        }
    }
}
