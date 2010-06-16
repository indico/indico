{
    checkParams : function () {
        return {};
    },

    errorHandler: function(event, error) {
    },

    customText : function(booking) {
    },

    onLoad : function() {
        // automatically scroll down to fit the page into one window
        document.getElementById('scroll_down').scrollIntoView(true);

        // make sure checkboxes are in agreement with default values
        // (these values are set at the end of NewBookingForm.tpl)
        $E('RMLanguagePrimary').dom.checked           = RMLanguageFlagPrimary;
        $E('RMLanguageSecondary').dom.checked         = RMLanguageFlagSecondary;
        $E('RMLanguageOther').dom.checked             = RMLanguageFlagOther;
        $E('RMLanguageOtherSelect').dom.selectedIndex = RMLanguageValueOther;
    }
}
