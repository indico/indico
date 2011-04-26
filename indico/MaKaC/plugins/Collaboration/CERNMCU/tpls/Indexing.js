{
    customText: function(booking) {
        if (!booking.error) {
            return "ID: " + booking.bookingParams.id + ", name: " + booking.bookingParams.name;
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
    }
}
