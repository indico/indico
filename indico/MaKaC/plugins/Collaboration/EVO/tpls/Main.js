{
    start : function(booking, iframeElement) {
        if (Browser.IE) {
            window.location.href = booking.url;
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
            'meetingTitle' : ['text', false],
            'meetingDescription' : ['text', false],
            
            'startDate' : ['datetime', false, function(startDateString, values){
                var errors = [];
                var startDate = IndicoUtil.parseDateTime(startDateString);
                              
                //check start date is not in the past
                var startDatePlusExtraTime = new Date();
                startDatePlusExtraTime.setTime(startDate.getTime() + <%= AllowedStartMinutes %> *60*1000);
                if (beforeNow(startDatePlusExtraTime)) {
                    errors.push($T("Start date cannot be before the past <%= AllowedStartMinutes %> minutes"));
                }
                
                // check start date is not before the minimum start date (event start date - <%= AllowedMarginMinutes %> min )
                if (startDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push($T("Start date cannot be <%= AllowedMarginMinutes %> minutes before the Indico event start date. Please choose it after <%= MinStartDate %>"));
                }
                
                // check start date is not after the maximum start date (event end date + <%= AllowedMarginMinutes %> min )
                if (startDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push($T("Start date cannot be <%= AllowedMarginMinutes %> minutes after the Indico event end date. Please choose it before <%= MaxEndDate %>"));
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
                    errors.push($T("End date cannot be before the past <%= AllowedStartMinutes %> minutes"));
                }
              
                // check end date is not after the maximum start date (event end date + <%= AllowedMarginMinutes %> min )
                if (endDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push($T("End date cannot be <%= AllowedMarginMinutes %> minutes after the Indico event end date. Please choose it before <%= MaxEndDate %>"));
                }
                
                // check start date is not before the minimum start date (event start date - <%= AllowedMarginMinutes %> min )
                if (endDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push($T("End date cannot be <%= AllowedMarginMinutes %> minutes before the Indico event start date. Please choose it after <%= MinStartDate %>"));
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
                CSErrorPopup($T("Meeting removed by EVO"), $T("This meeting seems to have been deleted in EVO for some reason.<br />") +
                        $T("Please delete it and try to create it again."));
            }
            if (error.errorType == 'changesFromEVO') {
                CSErrorPopup($T("Changes in the EVO server"), $T("This meeting seems to have been changes in EVO for some reason.<br />") +
                        $T("The fields that were changed are: ") + error.changes.join(', '));
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
            return booking.bookingParams.startDate.substring(11) + " to " + booking.bookingParams.endDate.substring(11) + " for " + booking.bookingParams.communityName;
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
        
        if (booking.changesFromEVO.length > 0) {
            infoHTML +=
            '<tr><td colspan="2">'+
                '<div class="collaborationWarning" style="display: inline;">' +
                    $T('Changed by EVO Staff:') + 
                    '<ul>'
            
            for (var i=0; i<booking.changesFromEVO.length; i++) {
                infoHTML +=
                        '<li>' +
                            booking.changesFromEVO[i] +            
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
            
            '<tr><td class="collaborationInfoLeftCol">' + $T('Community:') + '<\/td><td>' +
                booking.bookingParams.communityName +
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
                (booking.url? booking.url : $T("not assigned yet")) + 
            '<\/td><\/tr>'+
            
            '<tr><td class="collaborationInfoLeftCol">' + $T('Indico booking ID:') + '<\/td><td>' +
                booking.id + 
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
        return ["startDate", "endDate"]
    },
    
    getPopupDimensions: function() {
        return {width : 600, height: 260};
    },
    
    onCreate: function() {
        var startDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
        startDateHelpImg.dom.onmouseover = EVOStartDateHelpPopup;
        
        var endDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
        endDateHelpImg.dom.onmouseover = EVOEndDateHelpPopup;
        
        $E('startDateHelp').set(startDateHelpImg);
        $E('endDateHelp').set(endDateHelpImg);
    },
    
    onEdit: function() {
        callFunction('EVO','onCreate');
    },
    
    postCreate: function(booking) {
        
    },
    
    postEdit: function(booking) {

    },
    
    postDelete: function(booking) {
        if (booking.warning) {
            if (booking.warning.message === 'cannotDeleteNonExistant') {
                var popup = new AlertPopup("Booking deletion", Html.span({},"The booking was deleted successfully from Indico.",
                        Html.br(),
                        "However, please note that the booking had already been removed from the EVO system previously."));
                popup.open();
            }
        }
    }
}