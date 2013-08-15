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
            'startDate' : ['datetime', false, function(startDateString, values){
                var errors = [];
                var startDate = IndicoUtil.parseDateTime(startDateString);

                //check start date is not in the past
                // if (beforeNow(startDate)) {
                //    errors.push("Start date cannot be in the past")
                // }

                // check start date is not before the minimum start date (event start date)
                if (startDate < IndicoUtil.parseDateTime("${ MinStartDate }")) {
                    errors.push($T("Start date cannot be more than ${ ExtraMinutesBefore } minutes before the Indico event start date. Please choose it after ${ MinStartDate }"));
                }

                // check start date is not after the maximum start date (event end date)
                if (startDate > IndicoUtil.parseDateTime("${ MaxEndDate }")) {
                    errors.push($T("Start date cannot be more than ${ ExtraMinutesAfter } minutes after the Indico event end date. Please choose it before ${ MaxEndDate }"));
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

                // check start date is not after the maximum start date (event end date)
                if (endDate > IndicoUtil.parseDateTime("${ MaxEndDate }")) {
                    errors.push($T("End date cannot be more than ${ ExtraMinutesAfter } minutes after the Indico event end date. Please choose it before ${ MaxEndDate }"));
                }

                // check start date is not before the minimum start date (event start date)
                if (endDate < IndicoUtil.parseDateTime("${ MinStartDate }")) {
                    errors.push($T("End date cannot be more than ${ ExtraMinutesBefore } minutes before the Indico event start date. Please choose it after ${ MinStartDate }"));
                }


                // check start date is not after end date, if start date exists
                var startDate = IndicoUtil.parseDateTime(values["startDate"]);
                if (startDate) {
                    if (startDate > endDate) {
                        errors.push($T("End date cannot be before start date."));
                    }
                }

                return errors;
            }],
            'pin': ['non_negative_int', true, function(pin, values) {
                var errors = [];

                if (pin.length >= 32) {
                    errors.push($T("The pin cannot have more than 31 characters."));
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
                break;
            case 6:
                CSErrorPopup("MCU Error", [$T("There are too many conferences in the MCU. No more can be created right now.")]);
                break;
            case 7:
                CSErrorPopup("MCU Error", [$T("There are too many participants in the MCU. No more can be created right now.")]);
                break;
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
        var infoTbody = Html.tbody();

        if (booking.error) {
            var errorCell = Html.td({colspan:2, colSpan:2});

            switch(booking.faultCode) {
            case 2:
                errorCell.append(Html.span('collaborationWarning', $T("The Conference name already exists in the MCU. Please choose another one.")));
                break;
            case 18:
                errorCell.append(Html.span('collaborationWarning', $T("The Conference ID already exists in the MCU. Please choose another one.")));
                break;
            case 'tooManyTries':
                errorCell.append(Html.span('collaborationWarning', $T("Indico tried repeatedly to obtain a unique ID in the MCU and failed. Please contact Indico support.")));
                break;
            default:
                errorCell.append($T("MCU fault ") + booking.faultCode);
            }
            infoTbody.append(Html.tr({}, errorCell));
        }

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Conference name:')),
            Html.td({}, booking.error && booking.faultCode == 2 ?
                        Html.span('collaborationWarning', booking.bookingParams.name + $T(' (duplicated)')) :
                        booking.bookingParams.name )));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Start date:')),
            Html.td({}, formatDateStringCS(booking.bookingParams.startDate))));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('End date:')),
            Html.td({}, formatDateStringCS(booking.bookingParams.endDate))));

        var pinInfo;
        if (booking.bookingParams.hasPin) {
            pinInfo = new HiddenText(booking.bookingParams.pin, Html.span("HiddenPIN", "****"), false).draw();
        } else {
            pinInfo = $T("No PIN was defined");
        }

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Pin:')),
            Html.td({}, pinInfo)));

        var participantsInfo;
        if (booking.bookingParams.participants.length > 0) {
            participantsInfo = new CERNMCUBuildParticipantsInfo(booking).draw();
        } else {
            participantsInfo = $T("No participants have been configured yet.");
        }

        infoTbody.append(Html.tr({},
                Html.td("collaborationInfoLeftCol", $T('Participants:')),
                Html.td({}, participantsInfo)));

        infoTbody.append(Html.tr({},
                Html.td("collaborationInfoLeftCol", $T('MCU Conf. ID:')),
                Html.td({}, booking.error && booking.faultCode == 18 ?
                            Html.span('collaborationWarning', booking.bookingParams.id + $T(' (duplicated)')) :
                            booking.bookingParams.id ? booking.bookingParams.id : Html.span('collaborationWarning', $T('No ID yet')))));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Description:')),
            Html.td({}, booking.bookingParams.description)));


        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Visibility:')),
            Html.td({}, booking.bookingParams.hidden? $T("Hidden") : $T("Visible"))));

        if (!booking.error) {
            infoTbody.append(Html.tr({},
                Html.td("collaborationInfoLeftCol", $T('How to join:')),
                Html.td({},
                        $T('1) If you are registered in the CERN Gatekeeper, please dial ') + '${ CERNGatekeeperPrefix }' + booking.bookingParams.id,
                        Html.br(),
                        $T('2) If you have GDS enabled in your endpoint, please call ') + '${ GDSPrefix }' + booking.bookingParams.id,
                        Html.br(),
                        $T('3) Otherwise dial ') + '${ MCU_IP }' + $T(' and using FEC (Far-End Controls) with your remote, enter "') + booking.bookingParams.id + $T('" followed by the "#".'),
                        Html.br(),
                        $T('4) To join by phone dial ') + '${ Phone_number }' + $T(', enter "') + booking.bookingParams.id + $T('" followed by the "#".'))));
        }

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Created on:')),
            Html.td({}, formatDateTimeCS(booking.creationDate))));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Last modified on:')),
            Html.td({}, formatDateTimeCS(booking.modificationDate))));

        return Html.div({}, Html.table({}, infoTbody));
    },

    getDateFields : function() {
        return ["startDate", "endDate"]
    },

    onCreate : function(bookingPopup) {
        $E('autoYesRB').dom.checked = true;
        disableCustomId();
        % if IncludeInitialRoom:
            pf = new ParticipantListField([{type: 'room',
                                           name: "${escapeHTMLForJS(InitialRoomName)}",
                                           institution: "${escapeHTMLForJS(InitialRoomInstitution)}",
                                           ip: "${InitialRoomIP}",
                                           participantType: 'by_address'}])
            var ipRetrievalResult = ${ IPRetrievalResult }

            switch (ipRetrievalResult) {
            case 1:
                var popup = new AlertPopup($T("Room H.323 IP"), Html.span({}, $T("We have added this event's room as a participant."),
                                                                          Html.br(),
                                                                          $T("But it does not have an H.323 IP defined."),
                                                                          Html.br(),
                                                                          $T("Please remember to fill its IP by editing it.")));
                popup.open();
                break;
            case 2:
                CSErrorPopup("Room H.323 IP", [$T("The event's room has an H.323 IP defined, but it is not a valid IP."),
                                               $T("Please fill the IP yourself.")]);
                break;
            case 3:
                CSErrorPopup("Room H.323 IP", [$T("Indico could not retrieve the H.323 IP for this event's room."),
                                               $T("(Indico could not connect to its Room Booking database)"),
                                               $T("Please remember to fill its IP yourself by editing the room")])
                break;
            case 4:
                CSErrorPopup("Room H.323 IP", [$T("Indico could not retrieve the H.323 IP for this event's room."),
                                               $T("(Unknown problem when querying the Room Booking database)"),
                                               $T("Please remember to fill its IP yourself by editing the room.")]);
                break;
            default:
                break;
            }

        % else:
            pf = new ParticipantListField();
        % endif

        $E('participantsCell').set(pf.draw());

        var CERNMCUPinField = new ShowablePasswordField('pin', '', false);
        $E('PINField').set(CERNMCUPinField.draw());
        bookingPopup.addComponent(CERNMCUPinField);

        CERNMCUDrawContextHelpIcons();
    },

    onEdit: function(booking, bookingPopup) {
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

        var CERNMCUPinField = new ShowablePasswordField('pin', '', false);
        $E('PINField').set(CERNMCUPinField.draw());
        bookingPopup.addComponent(CERNMCUPinField);

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
                CSErrorPopup($T("Invalid participants"), [$T("There is more than one participant with the ip ") + participant.get("ip")]);
                break;
            } else if (!Util.Validation.isIPAddress(ip)) {
                CSErrorPopup($T("Invalid participants"), [$T("The participant ") + (i + 1) + $T(" does not have a correct IP")]);
                errors = true;
                break;
            } else {
                ips[participant.get("ip")] = true;
            }

        }

        return !errors;
    }
}
