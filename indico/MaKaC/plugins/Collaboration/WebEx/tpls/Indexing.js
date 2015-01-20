{
    "customText": function(booking, viewBy) {
        if (booking.error && booking.errorMessage) {
            return '<span class="collaborationWarning">' + booking.errorMessage + '<\/span>'
        } else {
            return "Title: " + booking.bookingParams.meetingTitle;
        }
    }
}
