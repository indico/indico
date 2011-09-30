{
    start : function(booking, iframeElement) {
        if (Browser.IE) {
            var popup = new EVOLaunchClientPopup(booking.url);
            popup.open();
        } else {
            iframeElement.location.href = booking.url;
        }
    },

    checkStart : function(booking) {
        booking.permissionToStart = true;
        return true;
    },

    checkParams: function() {
        return {
            'communityId': ['text', false, function(option, values){
                var errors = [];
                if (option == 'chooseOne') {
                    errors.push($T("Please choose a community."));
                }
                return errors;
            }],
            'meetingTitle' : ['text', false],
            'meetingDescription' : ['text', false],

            'startDate' : ['datetime', false, function(startDateString, values){
                var errors = [];
                var startDate = IndicoUtil.parseDateTime(startDateString);

                //check start date is not in the past
                var startDatePlusExtraTime = new Date();
                startDatePlusExtraTime.setTime(startDate.getTime() + (${ AllowedStartMinutes } - 1) *60*1000);
                if (beforeNow(startDatePlusExtraTime)) {
                    errors.push($T("Start date cannot be before the past ${ AllowedStartMinutes } minutes"));
                }

                // check start date is not before the minimum start date (event start date - ${ ExtraMinutesBefore } min )
                if (startDate < IndicoUtil.parseDateTime("${ MinStartDate }")) {
                    errors.push($T("Start date cannot be more than ${ ExtraMinutesBefore } minutes before the Indico event start date. Please choose it after ${ MinStartDate }"));
                }

                // check start date is not after the maximum start date (event end date + ${ ExtraMinutesAfter } min )
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

                //check end date is not in the past
                if (beforeNow(endDate)) {
                    errors.push($T("End date cannot be before the past ${ AllowedStartMinutes } minutes"));
                }

                // check end date is not after the maximum end date (event end date + ${ ExtraMinutesAfter } min )
                if (endDate > IndicoUtil.parseDateTime("${ MaxEndDate }")) {
                    errors.push($T("End date cannot be more than ${ ExtraMinutesAfter } minutes after the Indico event end date. Please choose it before ${ MaxEndDate }"));
                }

                // check start date is not before the minimum start date (event start date - ${ ExtraMinutesBefore } min )
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
            }]
        }
    },

    errorHandler: function(event, error) {
        if (event == 'create' || event == 'edit') {
            if (error.errorType == 'duplicated') {
                var message = $T('EVO considers this meeting duplicated. Please change either the title of the meeting, or its start and ending times.');
                IndicoUtil.markInvalidField($E('meetingTitle'), message);
                IndicoUtil.markInvalidField($E('startDate'), message);
                IndicoUtil.markInvalidField($E('endDate'), message);
            }

            if (error.errorType == 'overlapped') {
                var message = $T('The start and/or end times of this booking overlap with the booking with title "') +
                              error.overlappedBooking.bookingParams.meetingTitle +
                              '" (' + formatDateStringCS(error.overlappedBooking.bookingParams.startDate) +
                              $T(' to ') + formatDateStringCS(error.overlappedBooking.bookingParams.endDate) + ')'
                IndicoUtil.markInvalidField($E('startDate'), message);
                IndicoUtil.markInvalidField($E('endDate'), message);
            }

            if (error.errorType == 'start_in_past') {
                var message = $T('EVO considers that this meeting is starting too much in the past. Please change the start time.');
                IndicoUtil.markInvalidField($E('startDate'), message);
            }
        }

        if (event == 'checkStatus') {
            if (error.errorType == 'deletedByEVO') {
                CSErrorPopup($T("Meeting removed by EVO"),
                        [$T("This meeting seems to have been deleted in EVO for some reason."),
                         $T("Please delete it and try to create it again.")]);
            }
        }

        if (event == 'remove') {
            if (error.errorType == 'cannotDeleteOld') {
                CSErrorPopup($T("Cannot remove"), [$T("It is not possible to delete an old EVO meeting")]);
            }
            if (error.errorType == 'cannotDeleteOngoing') {
                CSErrorPopup($T("Cannot remove"), [$T("It is not possible to delete an ongoing EVO meeting")]);
            }
            if (error.errorType == 'cannotDeleteNonExistant') {
                CSErrorPopup($T("Cannot remove"), [$T("It seems that EVO meeting was already deleted by another party")]);
            }
        }
    },

    customText: function(booking) {
        if (booking.error && booking.errorMessage) {
            return '<span class="collaborationWarning">' + booking.errorMessage + '<\/span>'
        } else {
            return booking.bookingParams.startDate.split(' ')[1] + " to " + booking.bookingParams.endDate.split(' ')[1] + " for " + booking.bookingParams.communityName;
        }
    },

    showInfo : function(booking) {
        var infoTbody = Html.tbody();

        if (booking.error && booking.errorDetails) {
            var errorCell = Html.td({colspan:2, colSpan:2});
            errorCell.append(Html.span('collaborationWarning', booking.errorDetails));
            infoTbody.append(Html.tr({}, errorCell));
        }

        if (booking.changesFromEVO.length > 0) {
            var changesCell = Html.td({colspan:2, colSpan:2});
            var changesDiv = Html.div({className: 'collaborationWarning', style:{display:'inline'}});

            changesDiv.append(Html.span({}, $T('Changed by EVO Staff:')));
            var changesList = Html.ul();

            for (var i=0; i<booking.changesFromEVO.length; i++) {
                changesList.append(Html.li({}, booking.changesFromEVO[i]));
            }

            changesDiv.append(changesList);
            changesCell.append(changesDiv);
            infoTbody.append(Html.tr({}, changesCell));
        }

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Title:')),
            Html.td({}, booking.bookingParams.meetingTitle)));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Community:')),
            Html.td({}, booking.bookingParams.communityName)));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Start date:')),
            Html.td({}, formatDateStringCS(booking.bookingParams.startDate))));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('End date:')),
            Html.td({}, formatDateStringCS(booking.bookingParams.endDate))));

        var passwordInfo;
        if (booking.bookingParams.hasAccessPassword) {
            passwordInfo = new HiddenText(booking.bookingParams.accessPassword, Html.span("EVOHiddenPassword", "********"), false).draw();
        } else {
            passwordInfo = $T("No access password was defined");
        }

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Password:')),
            Html.td({}, passwordInfo)));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Phone Bridge ID:')),
            Html.td({}, booking.phoneBridgeId)));

        var phoneBridgePasswordInfo = null;
        if (exists(booking.phoneBridgePassword)) {
            phoneBridgePasswordInfo = new HiddenText(booking.phoneBridgePassword, Html.span("EVOHiddenPassword", "********"), false).draw();
        } else {
            phoneBridgePasswordInfo = $T("No access password was defined");
        }
        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Phone Bridge password:')),
            Html.td({}, phoneBridgePasswordInfo)));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Description:')),
            Html.td({}, booking.bookingParams.meetingDescription)));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Visibility:')),
            Html.td({}, booking.bookingParams.hidden? $T("Hidden") : $T("Visible"))));

        infoTbody.append(Html.tr({},
            Html.td("collaborationInfoLeftCol", $T('Auto-join URL:')),
            Html.td({}, booking.url ? Html.a({href:booking.url}, booking.url) : $T("not assigned yet"))));

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

    onCreate: function(bookingPopup) {
        var EVOPasswordField = new ShowablePasswordField('accessPassword', '', false);
        $E('passwordField').set(EVOPasswordField.draw());
        bookingPopup.addComponent(EVOPasswordField);

        EVODrawContextHelpIcons();
        % if not PossibleToCreateOrModify:
            var popup = new WarningPopup($T("Impossible to create an EVO booking"),
                    [$T("The start and ending dates of your event are in the past. " +
                        "It is not possible to create an EVO booking in the past " +
                        "or outside the start / ending times of your event."),
                     Html.br(),
                     $T("If you really need to create an EVO booking, please go first to " +
                        "the [[" + "${ GeneralSettingsURL }" + " General Settings]] page and change " +
                        "the start / end time of your event.")
                     ]);
            popup.open();
        % endif
    },

    onEdit: function(booking, bookingPopup) {
        var EVOPasswordField = new ShowablePasswordField('accessPassword', '', false);
        $E('passwordField').set(EVOPasswordField.draw());
        bookingPopup.addComponent(EVOPasswordField);

        EVODrawContextHelpIcons();
        % if not PossibleToCreateOrModify:
            var popup = new WarningPopup($T("Impossible to modify this EVO booking"),
                [$T("The start and ending dates of your event are in the past. " +
                    "It is not possible to modify an EVO booking in the past " +
                    "or outside the start / ending times of your event."),
                    Html.br(),
                 $T("If you really need to modify this EVO booking, please go first to " +
                    "the [[" + "${ GeneralSettingsURL }" + " General Settings]] page and change " +
                    "the start / end time of your event.")
                 ]);
            popup.open();
        % endif
    },

    postCheckStatus: function(booking) {
        if (booking.changesFromEVO.length > 0) {
            CSErrorPopup($T("Changes in the EVO server"),
                         [Html.span({}, $T("This meeting seems to have been changed in EVO for some reason."),
                                       Html.br(),
                                       $T("The fields that were changed are: ") + booking.changesFromEVO.join(', ') + "."),
                                       $T("You can also check them in the booking's details.")]);
        }
    },

    postDelete: function(booking) {
        if (booking.warning) {
            if (booking.warning.message === 'cannotDeleteNonExistant') {
                var popup = new AlertPopup($T("Booking deletion"),
                        Html.span({}, $T("The booking was deleted successfully from Indico."),
                                      Html.br(),
                                      $T("However, please note that the booking had already been removed from the EVO system previously.")));
                popup.open();
            }
        }
    }
}
