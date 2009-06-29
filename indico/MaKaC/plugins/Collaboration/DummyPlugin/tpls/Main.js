{
    "start" : function(booking, iframeElement) {
        iframeElement.location.href = "http://evo.caltech.edu/evoGate/koala.jnlp"
        //iframeElement.location.href = "http://www.google.com/search?q=" + booking.startParams.number
    },
    
    "stop" : function(booking, iframeElement) {
        $E("iframeTarget" + booking.id).dom.src = ""
    },
    
    "checkStart" : function(booking) {
        if (booking.bookingParams.favouriteColor == "blue") {
            return true;
        } else {
            alert("Why don't you like blue?");
            return false;
        }
    }
}