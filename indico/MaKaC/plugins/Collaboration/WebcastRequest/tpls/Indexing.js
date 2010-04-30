{
    "customText": function(booking, viewBy) {
        if (booking.statusMessage == "Request rejected by responsible" && booking.rejectionReason && trim(booking.rejectionReason)) {
            return "Rejection reason: " + trim(booking.rejectionReason);
        }
    }
}
