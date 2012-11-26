var vidyoOwnerField = null;

var vidyoMarkBookingNotPresent = function(booking) {
        booking.statusMessage = $T("Booking no longer exists");
        booking.statusClass = "statusMessageOther";
        booking.canBeStarted = false;
        refreshBookingM(booking, false);
}

/**
 * Mouseover help popup for the 'PIN' field
 */
var VidyoPINHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        $T('If you want to <strong>protect<\/strong> your Vidyo room with a PIN, please input it here. Otherwise, leave this field empty.')
    );
};

/**
 * Mouseover help popup for the 'Display PIN' checkbox
 */
var VidyoDisplayPinHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                $T("The public room's PIN will be displayed in the event page. " +
                   '<strong>Any person that can see the event page will see the PIN.</strong> Please use this option carefully.')
    );
};

/**
 * Mouseover help popup for the 'Display PIN' checkbox
 */
var VidyoOwnerHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                $T("This person will be the owner of the public room. This means that this person will be able to " +
                " invite people to the room, fix a maximum number of attendees, etc.")
    );
};

/**
 * Mouseover help popup for the 'displayURL' field
 */
var VidyoDisplayURLHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<div style="padding:3px; width: 200px;">' +
            $T('Please note that regardless of this option, '+
               'a <em>Join Now!</em> link will appear.') +
        '<\/div>');
};

/**
 * Draws the context help icons and assigns the appropiate popups to each one.
 */
var vidyoDrawContextHelpIcons = function() {
    $('#PINHelpImg').qtip({
        content : $T('If you want to <strong>protect<\/strong> your Vidyo room with a PIN, please input it here. Otherwise, leave this field empty.')});
    $('#moderatorPINHelpImg').qtip({
        content : $T('This is a moderator PIN. Users that know this PIN will be able to moderate the meeting')});
    $('#displayURLHelpImg').qtip({
        content : $T('Please note that regardless of this option, a <em>Join Now!</em> link will appear.')});
    $('#hiddenHelpImg').qtip({
        content : $T('This option hides the booking in the event page.')});
    $('#ownerHelpImg').qtip({
        content : $T("This person will be the owner of the public room. This means that this person will be able to " +
                     "invite people to the room, fix a maximum number of attendees, etc.")});
    $('#displayPinHelpImg').qtip({
        content : $T("The public room's PIN will be displayed in the event page. "
                     + "<strong>Any person that can see the event page will see the PIN.</strong> Please use this option carefully.")});
}
