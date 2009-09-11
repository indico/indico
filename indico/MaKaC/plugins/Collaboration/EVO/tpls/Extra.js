/**
 * Mouseover help popup for the 'Keep booking synchronized with event' advanced option
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
 * Mouseover help popup for the 'Keep booking hidden' advanced option
 */
var EVOEndDateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px">' + 
            $T('Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %>') + '<br \/>' +
            $T("(Allowed dates \/ times based on your event's start date and end date)") +
        '<\/div>');
};