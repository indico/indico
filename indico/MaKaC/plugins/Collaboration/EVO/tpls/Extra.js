var EVOPasswordField = null; //place where to keep a ShowablePasswordField object to access later

/**
 * Mouseover help popup for EVOLaunchClientPopup
 */

var EVOLaunchClientHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('If you are using Internet Explorer, Indico cannot load the EVO client directly;') + '<br \/>' +
            $T('you need to click on the link.') + '<br \/>' +
            $T('You can avoid this by using another browser. Sorry for the inconvenience.') +
        '<\/div>');
};

type("EVOLaunchClientPopup", ["ExclusivePopup"],
    {
        draw: function() {
            var self = this;

            var linkClicked = function(){
                self.close();return true;
            }

            var clientLink = Html.a({href: this.bookingUrl, onclick : linkClicked, style:{display: 'block'}},
                    $T("Click here to launch the EVO client"));

            var infoLink = Html.span({className: 'fakeLink', style: {display: 'block', fontSize: 'smaller', paddingTop: pixels(10)}},
                $T('(Why am I getting this popup?)'));
            infoLink.dom.onmouseover = EVOLaunchClientHelpPopup

            var cancelButton = Html.button({style: {marginTop: pixels(10)}}, $T("Cancel"));
            cancelButton.observeClick(function(){
                self.close();
            });

            return this.ExclusivePopup.prototype.draw.call(this,
                    Html.div({style:{textAlign: 'center'}}, clientLink, infoLink, cancelButton)
                    );
        }
    },
    function(bookingUrl) {
        this.bookingUrl = bookingUrl;
        this.ExclusivePopup($T('Launch EVO client'), positive);
    }
);

/**
 * Mouseover help popup for the 'Start date' field
 */
var EVOStartDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %>.') + '<br \/>' +
            $T("(Allowed dates \/ times based on your event's start date and end date)") + '<br \/>' +
            $T('Also remember the start date cannot be more than <%= AllowedStartMinutes %> in the past.') +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'End date' field
 */
var EVOEndDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %>') + '<br \/>' +
            $T("(Allowed dates \/ times based on your event's start date and end date)") +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'password' field
 */
var EVOPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('If you want to <strong>protect<\/strong> your EVO meeting with a password, please input it here. Otherwise, leave this field empty.') +
        '<\/div>');
};


/**
 * Mouseover help popup for the 'displayPassword' field
 */
var EVODisplayPasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('The EVO Meeting password will be displayed <strong><em>in clear</em></strong> in the event display page. '+
               'Any person that can see the event page will see the password. Please use this option carefully.') +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'displayPhonePassword' field
 */
var EVODisplayPhonePasswordHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
        $T('The Phone bridge password will be displayed <strong><em>in clear</em></strong> in the event display page. '+
           'Any person that can see the event page will see the password. Please use this option carefully.') +
        '<\/div>');
};

/**
 * Mouseover help popup for the 'displayURL' field
 */
var EVODisplayURLHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' +
            $T('The auto-join URL will be displayed. Please note that when it is possible to join the EVO meeting, '+
               'a <em>Join Now!</em> link will appear. People will be able to join the meeting by clicking on this link.') +
        '<\/div>');
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
