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

    }
}