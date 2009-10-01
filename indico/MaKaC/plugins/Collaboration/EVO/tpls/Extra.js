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
 * Draws the context help icons and assigns the appropiate popups to each one.
 */
var EVODrawContextHelpIcons = function() {
    var startDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    startDateHelpImg.dom.onmouseover = EVOStartDateHelpPopup;
    
    var endDateHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    endDateHelpImg.dom.onmouseover = EVOEndDateHelpPopup;
    
    var passwordHelpImg = Html.img({src: imageSrc("help"), style: {marginLeft: '5px', verticalAlign: 'middle'}});
    passwordHelpImg.dom.onmouseover = EVOPasswordHelpPopup;
    
    $E('startDateHelp').set(startDateHelpImg);
    $E('endDateHelp').set(endDateHelpImg);
    $E('passwordHelp').set(passwordHelpImg);
}