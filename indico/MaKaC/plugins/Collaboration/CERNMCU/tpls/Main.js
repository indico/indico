{
    start : function(booking, iframeElement) {
        
    },
        
    checkStart : function(booking) {
        booking.permissionToStart = true;
        return true;
    },
    
    checkParams: function() {
        return {
            'name' : ['text', false],
            'description' : ['text', false],
            'customId' : ['text', true, function(customId, values){
                errors = []
                if (values["autoGenerateId"] == 'no') {
                    if (!trim(customId)) {
                        errors.push('Please introduce a numeric ID')
                    } else if (!IndicoUtil.isInteger(customId)) {
                        errors.push('Field must be a number');
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
                    errors.push("Start date cannot be before the Indico event start date. Please choose it after <%= MinStartDate %>");
                }
                
                // check start date is not after the maximum start date (event end date)
                if (startDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push("Start date cannot be after the Indico event end date. Please choose it before <%= MaxEndDate %>");
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
                
                //check start date is not in the past
                if (beforeNow(endDate)) {
                    errors.push("End date cannot be in the past")
                }
                
                // check start date is not before the minimum start date (event start date)
                if (endDate < IndicoUtil.parseDateTime("<%= MinStartDate %>")) {
                    errors.push("End date cannot be before the Indico event start date. Please choose it after <%= MinStartDate %>");
                }
                
                // check start date is not after the maximum start date (event end date)
                if (endDate > IndicoUtil.parseDateTime("<%= MaxEndDate %>")) {
                    errors.push("End date cannot be after the Indico event end date. Please choose it before <%= MaxEndDate %>");
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
    
    errorHandler : function(event, error){
        if (event == 'create' || event == 'edit') {
            switch (error.faultCode) {
            case 2:
                IndicoUtil.markInvalidField($E('title'), "This conference title already exists in the MCU. Please choose a different one.");
                break;
            case 18:
                if ($E('autoYesRB').dom.checked) {
                    CSErrorPopup("Indico was not able to find an unoccupied ID in the MCU");
                } else {
                    IndicoUtil.markInvalidField($E('customId'), "This conference ID already exists in the MCU. Please a different one.");
                }
                break;
            default:
                CSErrorPopup("MCU Error, code: " + error.faultCode);
            }
        } else {
            CSErrorPopup("MCU Error, code: " + error.faultCode);
        }
    },
    
    customText: function(booking) {
        if (!booking.error) {
            return "ID: " + booking.bookingParams.id;
        } else {
            var customText = '<span class="collaborationWarning">';
            switch(booking.faultCode) {
            case 2:
                customText += "Duplicated Name"
                break;    
            case 18:
                customText += "Duplicated ID"
                break;
            default:
                customText += booking.faultString;
            }
            customText += '<\/span>';
            return customText;
        }
    },
    
    showInfo : function(booking) {
        infoHTML = '<ul class="collaborationInfo">';
        
        if (booking.error) {
            infoHTML +=
                '<li class="collaborationInfo">'+
                    '<span class="collaborationWarning">';
            
            switch(booking.faultCode) {
            case 2:
                infoHTML += "The Conference name already exists in the MCU. Please choose another one."
                break;    
            case 18:
                infoHTML += "The Conference ID already exists in the MCU. Please choose another one."
                break;
            case 'tooManyTries':
                infoHTML += "Indico tried repeatedly to obtain a unique ID in the MCU and failed. Please contact Indico support."
                break;
            default:
                alert('default')
            }
            infoHTML +=
                    '<\/span>' +
                '<\/li>'
        }
        
        infoHTML +=
             '<li class="collaborationInfo">'+
                '<strong>Conference name: <\/strong>' +
                (booking.error && booking.faultCode == 2 ?
                    '<span class="collaborationWarning">' + booking.bookingParams.name + ' (duplicated)<\/span>' :
                    booking.bookingParams.name) +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Conference description: <\/strong>' +
                booking.bookingParams.description +
            '<\/li>'+
            
            '<li class="collaborationInfo">'+
                '<strong>Conference id: <\/strong>' +
                (booking.error && booking.faultCode == 18 ?
                        '<span class="collaborationWarning">' + booking.bookingParams.id + ' (duplicated)<\/span>' :
                        (booking.bookingParams.id ? booking.bookingParams.id : ('<span class="collaborationWarning">No ID yet<\/span>'))) +
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
                '<strong>PIN: <\/strong>' +
                (booking.bookingParams.hasPin? "PIN hidden" : "No PIN was defined") + 
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
    },
    
    onCreate : function() {
        $E('autoYesRB').dom.checked = true;
        <% if IncludeInitialRoom: %>
            pf = new ParticipantListField([{type: 'room',
                                           name: "<%= InitialRoomName %>",
                                           institution: "<%= InitialRoomInstitution %>",
                                           ip: "<%= InitialRoomIP %>"}]) 
        <% end %>
        <% else: %>
            pf = new ParticipantListField();
        <% end %>
        
        $E('participantsCell').set(pf.draw());
    },
    
    onEdit: function(booking) {
        if (booking.bookingParams.autoGenerateId == 'no') {
            enableCustomId();
        }
        
        pf = new ParticipantListField(booking.bookingParams.participants)
        $E('participantsCell').set(pf.draw());
    },
    
    onSave: function(values) {
        values["participants"] = pf.getParticipants()
    }
}