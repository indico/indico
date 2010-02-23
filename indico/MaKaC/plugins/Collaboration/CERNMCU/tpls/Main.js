{
    start : function(booking, iframeElement) {

    },

    checkStart : function(booking) {
        booking.permissionToStart = true;
        return true;
    },

    checkParams: function() {
        return {
            'name' : ['text', false, function(name, values){
                errors = [];
                if (name.length >= 32) {
                    errors.push($T("The name of the conference cannot have more than 31 characters."))
                }
                return errors;
            }],
            'description' : ['text', false],
            'customId' : ['text', true, function(customId, values){
                errors = [];
                if (values["autoGenerateId"] == 'no') {
                    if (!trim(customId)) {
                        errors.push($T('Please introduce a numeric ID.'));
                    } else if (!IndicoUtil.isInteger(customId)) {
                        errors.push($T('Field must be a number.'));
                    } else if (trim(customId).length != 5) {
                        errors.push($T('The id must have 5 digits.'));
                    }
                }
                return errors;
            }],
            'pin': ['text', true, function(pin, values){
                errors = [];
                if (exists(pin) && pin !== '') {
                    if (!IndicoUtil.isInteger(pin)) {
                        errors.push($T('The pin has to be a number.'));
                    }
                    if (pin.length >= 32) {
                        errors.push($T("The pin cannot have more than 31 characters."));
                    }
                }
                return errors;
            }],
            'startDate' : ['datetime', false, function(startDateString, values){
                var errors = [];
                var startDate = IndicoUtil.parseDateTime(startDateString);

                //check start date is not in the past
                // if (beforeNow(startDate)) {
                //    errors.push("Start date cannot be in the past")
                // }

                // check start date is not before the minimum start date (event start date)
                if (startDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push($T("Start date cannot be before the Indico event start date. Please choose it after <%= MinStartDate %>"));
                }

                // check start date is not after the maximum start date (event end date)
                if (startDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push($T("Start date cannot be after the Indico event end date. Please choose it before <%= MaxEndDate %>"));
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

                //check start date is not in the past
                if (beforeNow(endDate)) {
                    errors.push($T("End date cannot be in the past"));
                }

                // check start date is not before the minimum start date (event start date)
                if (endDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push($T("End date cannot be before the Indico event start date. Please choose it after <%= MinStartDate %>"));
                }

                // check start date is not after the maximum start date (event end date)
                if (endDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push($T("End date cannot be after the Indico event end date. Please choose it before <%= MaxEndDate %>"));
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

    errorHandler : function(event, error){
        if (event == 'create' || event == 'edit') {
            switch (error.faultCode) {
            case 2:
                IndicoUtil.markInvalidField($E('title'), $T("This conference title already exists in the MCU. Please choose a different one."));
                break;
            case 3:
                CSErrorPopup("MCU Error", [$T("Participant with IP ") + error.info + $T(" already exists in the MCU.")]);
            case 6:
                CSErrorPopup("MCU Error", [$T("There are too many conferences in the MCU. No more can be created right now.")]);
            case 7:
                CSErrorPopup("MCU Error", [$T("There are too many participants in the MCU. No more can be created right now.")]);
            case 18:
                if ($E('autoYesRB').dom.checked) {
                    CSErrorPopup("MCU Error", [$T("Indico was not able to find an unoccupied ID in the MCU")]);
                } else {
                    IndicoUtil.markInvalidField($E('customId'), $T("This conference ID already exists in the MCU. Please a different one."));
                }
                break;
            default:
                CSErrorPopup("MCU Error, code: " + error.faultCode, []);
            }
        } else {
            CSErrorPopup("MCU Error, code: " + error.faultCode, []);
        }
    },

    customText: function(booking) {
        if (!booking.error) {
            return "ID: " + booking.bookingParams.id + ". " + booking.bookingParams.participants.length + $T(" participants.");
        } else {
            var customText = '<span class="collaborationWarning">';
            switch(booking.faultCode) {
            case 2:
                customText += $T("Duplicated Name")
                break;
            case 18:
                customText += $T("Duplicated ID")
                break;
            default:
                customText += booking.faultString;
            }
            customText += '<\/span>';
            return customText;
        }
    },

    showInfo : function(booking) {
        infoHTML = '<div><table><tbody>';

        if (booking.error) {
            infoHTML +=
                '<tr><td colspan="2">'+
                    '<span class="collaborationWarning">';

            switch(booking.faultCode) {
            case 2:
                infoHTML += $T("The Conference name already exists in the MCU. Please choose another one.");
                break;
            case 18:
                infoHTML += $T("The Conference ID already exists in the MCU. Please choose another one.");
                break;
            case 'tooManyTries':
                infoHTML += $T("Indico tried repeatedly to obtain a unique ID in the MCU and failed. Please contact Indico support.");
                break;
            default:
                alert('default')
            }
            infoHTML +=
                    '<\/span>' +
                '<\/td><\/tr>'
        }

        infoHTML +=
             '<tr><td class="collaborationInfoLeftCol">' + $T('Conference name:') + '<\/td><td>' +
                (booking.error && booking.faultCode == 2 ?
                    '<span class="collaborationWarning">' + booking.bookingParams.name + ' (duplicated)<\/span>' :
                    booking.bookingParams.name) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Conference description:') + '<\/td><td>' +
                booking.bookingParams.description +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Conference MCU ID:') + '<\/td><td>' +
                (booking.error && booking.faultCode == 18 ?
                        '<span class="collaborationWarning">' + booking.bookingParams.id + ' (duplicated)<\/span>' :
                        (booking.bookingParams.id ? booking.bookingParams.id : ('<span class="collaborationWarning">' + $T('No ID yet') + '<\/span>'))) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Start date:') + '<\/td><td>' +
                formatDateStringCS(booking.bookingParams.startDate) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('End date:') + '<\/td><td>' +
                formatDateStringCS(booking.bookingParams.endDate) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('PIN:') + '<\/td><td>' +
                (booking.bookingParams.hasPin? $T("PIN hidden") : $T("No PIN was defined")) +
            '<\/td><\/tr>'+

            '<tr><td class="collaborationInfoLeftCol">' + $T('Visibility') + '<\/td><td>' +
                (booking.bookingParams.hidden? $T("Hidden") : $T("Visible")) +
            '<\/td><\/tr>';

        if (!booking.error) { infoHTML +=

            '<tr><td class="collaborationInfoLeftCol">' + $T('How to join:') + '<\/td><td>' +
                $T('1) If you are registered in the CERN Gatekeeper, please dial ') + '<%= CERNGatekeeperPrefix %>' + booking.bookingParams.id + '<br \/>' +
                $T('2) If you have GDS enabled in your endpoint, please call ') + '<%= GDSPrefix %>' + booking.bookingParams.id + '<br \/>' +
                $T('3) Otherwise dial ') + '<%= MCU_IP %>' + $T(' and using FEC (Far-End Controls) with your remote, enter "') + booking.bookingParams.id + $T('" followed by the "#".<br \/>') +
                $T('4) To join by phone dial ') + '<%= Phone_number %>' + $T(', enter "') + booking.bookingParams.id + $T('" followed by the "#".') +
             '<\/td><\/tr>';
        }

        infoHTML +=
            '<tr><td class="collaborationInfoLeftCol">' + $T('Indico booking ID:') + '<\/td><td>' +
                booking.id +
            '<\/td><\/tr>' +

            '<tr><td class="collaborationInfoLeftCol">' + $T('Booking created on:') + '<\/td><td>' +
                formatDateTimeCS(booking.creationDate) +
            '<\/td><\/tr>' +

            '<tr><td class="collaborationInfoLeftCol">' + $T('Booking last modified on:') + '<\/td><td>' +
                formatDateTimeCS(booking.modificationDate) +
            '<\/td><\/tr>' +

        '<\/tbody><\/table><\/div>'

        return infoHTML;
    },

    getPopupDimensions: function() {
        if (Browser.IE) {
                var height = 370;
        } else {
                var height = 390;
        }
        return {width : 600, height: height};
    },

    getDateFields : function() {
        return ["startDate", "endDate"]
    },

    onCreate : function() {
        $E('autoYesRB').dom.checked = true;
        disableCustomId();
        <% if IncludeInitialRoom: %>
            pf = new ParticipantListField([{type: 'room',
                                           name: "<%= InitialRoomName %>",
                                           institution: "<%= InitialRoomInstitution %>",
                                           ip: "<%= InitialRoomIP %>"}])
            var ipRetrievalResult = <%= IPRetrievalResult %>

            switch (ipRetrievalResult) {
            case 1:
                var popup = new AlertPopup("Room H.323 IP", Html.span({},"We have added this event's room as a participant.",
                                                                          Html.br(),
                                                                          "But it does not have an H.323 IP defined.",
                                                                          Html.br(),
                                                                          "Please remember to fill its IP by editing it."));
                popup.open();
                break;
            case 2:
                CSErrorPopup("Room H.323 IP", ["The event's room doesn't has an H.323 IP defined, but it's not a valid IP.",
                                               "Please fill the IP yourself."]);
                break;
            case 3:
                CSErrorPopup("Room H.323 IP", ["Indico could not retrieve the H.323 IP for this event's room.",
                                               "(Indico could not connect to its Room Booking database)",
                                               "Please remember to fill its IP yourself by editing the room"])
                break;
            case 4:
                CSErrorPopup("Room H.323 IP", ["Indico could not retrieve the H.323 IP for this event's room.",
                                               "(Unknown problem when querying the Room Booking database)",
                                               "Please remember to fill its IP yourself by editing the room."]);
                break;
            default:
                break;
            }

        <% end %>
        <% else: %>
            pf = new ParticipantListField();
        <% end %>

        $E('participantsCell').set(pf.draw());

        CERNMCUDrawContextHelpIcons();
    },

    onEdit: function(booking) {
        // setFormValues has problems with radio buttons constructed with .innerHTML in IE7
        if (Browser.IE) {
            if (booking.bookingParams.autoGenerateId == 'no') {
                $E('autoNoRB').dom.checked = true;
                $E('autoYesRB').dom.checked = false;
            } else {
                $E('autoNoRB').dom.checked = false;
                $E('autoYesRB').dom.checked = true;
            }
        }

        if (booking.bookingParams.autoGenerateId == 'no') {
            enableCustomId();
        } else {
            disableCustomId();
        }

        pf = new ParticipantListField(booking.bookingParams.participants)
        $E('participantsCell').set(pf.draw());

        CERNMCUDrawContextHelpIcons();
    },

    onSave: function(values) {
        var participants = pf.getParticipants();
        values["participants"] = participants;

        var ips = {}
        var errors = false;
        for (var i = 0; i < participants.length.get(); i++) {
            var participant = participants.item(i).get();
            ip = participant.get("ip");
            if (participant.get("ip") in ips) {
                errors = true;
                CSErrorPopup("Invalid participants", ["There is more than one participant with the ip " + participant.get("ip")]);
                break;
            } else if (!Util.Validation.isIPAddress(ip)) {
                CSErrorPopup("Invalid participants", ["The participant " + (i + 1) + " does not have a correct IP"]);
                errors = true;
                break;
            } else {
                ips[participant.get("ip")] = true;
            }

        }

        return !errors;
    }
}