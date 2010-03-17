{
    checkParams : function () {
        return {
        }
    },

    errorHandler: function(event, error) {

    },

    customText : function(booking) {
        if (booking.acceptRejectStatus === false && trim(booking.rejectionReason)) {
            return $T("Rejection reason: ") + trim(booking.rejectionReason);
        }
    },

    clearForm : function () {

    },

    onLoad : function() {
        // automatically scroll down to fit the page into one window
        document.getElementById('scroll_down').scrollIntoView(true)
    }
}