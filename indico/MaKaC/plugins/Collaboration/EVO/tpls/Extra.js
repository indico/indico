/**
 * Mouseover help popup for EVOLaunchClientPopup
 */

var EVOLaunchClientHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('If you are using Internet Explorer, Indico cannot load the EVO client directly; '  +
            'you need to click on the link. ' +
            'You can avoid this by using another browser. Sorry for the inconvenience.'));
};

type("EVOLaunchClientPopup", ["AlertPopup"],
    {
        __getContent: function() {
            var self = this;

            var linkClicked = function(){
                self.close();
                return true;
            };

            var clientLink = $('<a/>', {href: this.bookingUrl})
                .click(linkClicked)
                .css('display', 'block')
                .text($T("Click here to launch the EVO client"));

            var infoLink = $('<span/>', {'class': 'fakeLink'})
                .mouseover(EVOLaunchClientHelpPopup)
                .css({
                    display: 'block',
                    fontSize: 'smaller',
                    paddingTop: '10px'
                })
                .text($T('(Why am I getting this popup?)'));

            return $('<div/>').append(clientLink).append(infoLink);
        }
    },
    function(bookingUrl) {
        this.bookingUrl = bookingUrl;
        this.AlertPopup($T('Launch EVO client'), this.__getContent());
    }
);

/**
 * Mouseover help popup for the 'Start date' field
 */
var EVOStartDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('Please create your booking between <strong>${ MinStartDate }</strong> and <strong>${ MaxEndDate }</strong> ' +
            "(Allowed dates \/ times based on your event's start date and end date). " +
            'Also, please remember the start date cannot be more than ${ AllowedStartMinutes } minutes in the past.')
    );
};

/**
 * Mouseover help popup for the 'End date' field
 */
var EVOEndDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('Please create your booking between <strong>${ MinStartDate }</strong> and <strong>${ MaxEndDate }</strong> ' +
            "(Allowed dates \/ times based on your event's start date and end date).")
    );
};

/**
 * Mouseover help popup for the 'password' field
 */
var EVOPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('If you want to <strong>protect<\/strong> your EVO meeting with a password, please input it here. ' +
                    'Otherwise, leave this field empty.'));
};


/**
 * Mouseover help popup for the 'displayPassword' field
 */
var EVODisplayPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('The EVO Meeting password will be displayed in the event page. '+
               '<strong>Any person that can see the event page will see the password.</strong> Please use this option carefully.')
    );
};

/**
 * Mouseover help popup for the 'displayPhonePassword' field
 */
var EVODisplayPhonePasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('The Phone bridge password will be displayed in the event page. '+
           '<strong>Any person that can see the event page will see the password.</strong> Please use this option carefully.')
    );
};

/**
 * Mouseover help popup for the 'displayURL' field
 */
var EVODisplayURLHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
            $T('Please note that regardless of this option, when the EVO meeting starts, '+
               'a <em>Join Now!</em> link will appear.')
    );
};

/**
 * Draws the context help icons and assigns the appropiate popups to each one.
 */
var EVODrawContextHelpIcons = function() {

    $E('startDateHelpImg').dom.onmouseover = EVOStartDateHelpPopup;
    $E('endDateHelpImg').dom.onmouseover = EVOEndDateHelpPopup;
    $E('passwordHelpImg').dom.onmouseover = EVOPasswordHelpPopup;
    $E('displayPasswordHelpImg').dom.onmouseover = EVODisplayPasswordHelpPopup;
    $E('displayPhonePasswordHelpImg').dom.onmouseover = EVODisplayPhonePasswordHelpPopup;
    $E('displayURLHelpImg').dom.onmouseover = EVODisplayURLHelpPopup;
}
