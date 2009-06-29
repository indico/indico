{
    "start" : function(booking, iframeElement) {
        if (Browser.IE) {
            window.location.href = booking.url;
        } else {
            iframeElement.location.href = booking.url;
        }
    },
        
    "checkStart" : function(booking) {
        booking.permissionToStart = true;
        return true;
    },
    
    "checkParams": function() {
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
                    errors.push("Start date cannot be before the past <%= AllowedStartMinutes %> minutes")
                }
                
                // check start date is not before the minimum start date (event start date - <%= AllowedMarginMinutes %> min )
                if (startDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push("Start date cannot be <%= AllowedMarginMinutes %> minutes before the Indico event start date. Please choose it after <%= MinStartDate %>");
                }
                
                // check start date is not after the maximum start date (event end date + <%= AllowedMarginMinutes %> min )
                if (startDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push("Start date cannot be <%= AllowedMarginMinutes %> minutes after the Indico event end date. Please choose it before <%= MaxEndDate %>");
                }
                
                // check start date is not after end date, if end date exists
                var endDate = IndicoUtil.parseDateTime(values["endDate"]);
                if (endDate) {
                    if (startDate > endDate) {
                        errors.push("End date cannot be before start date.")
                    }
                }
                
                return errors;
            }],
            
            'endDate' : ['datetime', false, function(endDateString, values){
                var errors = [];
                var endDate = IndicoUtil.parseDateTime(endDateString);
                              
                //check end date is not in the past
                if (beforeNow(endDate)) {
                    errors.push("End date cannot be before the past <%= AllowedStartMinutes %> minutes")
                }
              
                // check end date is not after the maximum start date (event end date + <%= AllowedMarginMinutes %> min )
                if (endDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push("End date cannot be <%= AllowedMarginMinutes %> minutes after the Indico event end date. Please choose it before <%= MaxEndDate %>");
                }
                
                // check start date is not before the minimum start date (event start date - <%= AllowedMarginMinutes %> min )
                if (endDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push("End date cannot be <%= AllowedMarginMinutes %> minutes before the Indico event start date. Please choose it after <%= MinStartDate %>");
                }
              
                // check start date is not after end date, if start date exists
                var startDate = IndicoUtil.parseDateTime(values["startDate"]);
                if (startDate) {
                    if (startDate > endDate) {
                        errors.push("End date cannot be before start date.")
                    }
                }
              
                return errors;
            }]
        }
    },
    
    errorHandler: function(event, error) {
        if (event == 'create' || event == 'edit') {
            if (error.errorType == 'duplicated') {
                var message = 'EVO considers this meeting duplicated. Please change either the title of the meeting, ' +
                              'or its start and ending times.'
                IndicoUtil.markInvalidField($E('meetingTitle'), message);
                IndicoUtil.markInvalidField($E('startDate'), message);
                IndicoUtil.markInvalidField($E('endDate'), message);
            }
            
            if (error.errorType == 'overlapped') {
                var message = 'The start and/or end times of this booking overlap with the booking with title "' + 
                              error.overlappedBooking.bookingParams.meetingTitle +
                              '" (' + formatDateStringCS(error.overlappedBooking.bookingParams.startDate) + 
                              ' to ' + formatDateStringCS(error.overlappedBooking.bookingParams.endDate) + ')'
                IndicoUtil.markInvalidField($E('startDate'), message);
                IndicoUtil.markInvalidField($E('endDate'), message);
            }
        }
        
        if (event == 'checkStatus') {
            if (error.errorType == 'deletedByEVO') {
                CSErrorPopup("Meeting removed by EVO", "This meeting seems to have been deleted in EVO for some reason.<br />"+
                        "Please delete it and try to create it again.");
            }
            if (error.errorType == 'changesFromEVO') {
                CSErrorPopup("Changes in the EVO server", "This meeting seems to have been changes in EVO for some reason.<br />"+
                             "The fields that were changed are: " + error.changes.join(', '));
            }
        }
        
        if (event == 'remove') {
            if (error.errorType == 'cannotDeleteOld') {
                CSErrorPopup("Cannot remove", ["It is not possible to delete an old EVO meeting"]);
            }
            if (error.errorType == 'cannotDeleteOngoing') {
                CSErrorPopup("Cannot remove", ["It is not possible to delete an ongoing EVO meeting"]);
            }
        }
    },
    
    "customText": function(booking) {
        if (booking.error && booking.errorMessage) {
            return '<span class="collaborationWarning">' + booking.errorMessage + '<\/span>'
        } else {
            return booking.bookingParams.startDate.substring(11) + " to " + booking.bookingParams.endDate.substring(11) + " for " + booking.bookingParams.communityName;
        }
    },
    
    "showInfo" : function(booking) {
        infoHTML = '<ul class="collaborationInfo">';
        
        if (booking.error && booking.errorDetails) {
            infoHTML +=
            '<li class="collaborationInfo">'+
                '<span class="collaborationWarning">' +
                    booking.errorDetails +
                '<\/span>' +
            '<\/li>'
        }
        
        if (booking.changesFromEVO.length > 0) {
            infoHTML +=
            '<li class="collaborationInfo">'+
                '<div class="collaborationWarning" style="display: inline;">' +
                    'Changed by EVO Staff:' + 
                    '<ul>'
            
            for (var i=0; i<booking.changesFromEVO.length; i++) {
                infoHTML +=
                        '<li class="collaborationInfo">' +
                            booking.changesFromEVO[i] +            
                        '<\/li>'
            }
            
            infoHTML +=
                    '<\/ul>' +
                '<\/div>' +
            '<\/li>'
        }
        
        infoHTML +=
             '<li class="collaborationInfo">'+
                '<strong>Meeting title: <\/strong>' +
                booking.bookingParams.meetingTitle +
            '<\/li>'+
    
            '<li class="collaborationInfo">'+
                '<strong>Start date: <\/strong>' +
                formatDateStringCS(booking.bookingParams.startDate) +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>End date: <\/strong>' +
                formatDateStringCS(booking.bookingParams.endDate) +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Community: <\/strong>' +
                booking.bookingParams.communityName +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Meeting description: <\/strong>' +
                booking.bookingParams.meetingDescription +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Access password: <\/strong>' +
                (booking.bookingParams.hasAccessPassword? "Access password hidden" : "No access password was defined") + 
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Auto-join URL: <\/strong>' +
                (booking.url? booking.url : "not assigned yet") + 
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Indico booking ID: <\/strong>' +
                booking.id + 
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Booking created on: <\/strong>' +
                formatDateTimeCS(booking.creationDate) +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Booking last modified on: <\/strong>' +
                formatDateTimeCS(booking.modificationDate) +
            '<\/li>'+

        '<\/ul>'
            
        return infoHTML;
    },
    
    getDateFields : function() {
        return ["startDate", "endDate"]
    }
}