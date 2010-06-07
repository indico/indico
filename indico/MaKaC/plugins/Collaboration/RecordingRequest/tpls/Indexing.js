{
    "customText": function(booking, viewBy) {
        if (booking.statusMessage == "Request rejected by responsible" && booking.rejectReason && trim(booking.rejectReason)) {
            return "Rejection reason: " + trim(booking.rejectReason);
        }
    }
}
