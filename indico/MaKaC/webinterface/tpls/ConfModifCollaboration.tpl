<% singleBookingPluginCount = len(SingleBookingPlugins) %>
<% multipleBookingPluginCount = len(MultipleBookingPlugins) %>
<% allPluginCount = singleBookingPluginCount + multipleBookingPluginCount %>

% if singleBookingPluginCount > 0:
    <%include file="ConfModifCollaborationSingleBookings.tpl"/>
% endif

% if multipleBookingPluginCount > 0 :
    % if singleBookingPluginCount > 0:
    <div class="horizontalLine" style="margin-top:1em;margin-bottom:1em;"></div>
    % endif

    <%include file="ConfModifCollaborationMultipleBookings.tpl"/>

% endif

<div id="iframes" style="display: none;">
</div>

<script type="text/javascript">

/* ------------------------------ GLOBAL VARIABLES ------------------------------- */

/**
 * Various JS functions that will be executed after actions. They depend on the booking type.
 * "start" : function(booking, iframeElement) { ... } : local actions to be executed when a booking is started.
 *           Should only be present when booking.hasStart is true.
 * "stop" : function(booking, iframeElement) { ... } : local actions to be executed when a booking is stopped
 *          Should only be present when booking.hasStop is true.
 * "checkStart" : function(booking) { --- } : checks if the current properties of the booking are good in order for the booking to start.
 *                Its presence is optional (if it is not present, the booking will be started without check).
 *                It is executed BEFORE the server start call, if there is one, and the client start call.
 *                If the booking is OK to start, it should:
 *                    -set booking.permissionToStart to true
 *                   -return true
 *                Otherwise returning false will cause the booking not to start.
 * "checkParams" : function (values) { ... } : checks the booking parameters when adding or editing a booking.
 *                 Its presence is optional (if it is not present, the booking will be passed to the server without check).
 *                 It has to return an array of strings with the errors detected.
 *                 If there are no errors detected, it should return an empty array [] .
 * "customText": function(booking) { ... } : returns text that will be displayed in the line represented the booking.
 *               Its presence is optional (if it is not present, no custom text will be displayed).
 */
var codes = {
${ ",\n". join(['"' + pluginId + '" \x3a ' + code for pluginId, code in JSCodes.items()]) }
}

/**
 * Dictionary that stores if for a given plugin name, its bookings should be able to be notified
 * of the parent event changing dates / timezones.
 */
var canBeNotifiedOnDateChanges = {
     ${ ",\n". join(['"' + pluginId + '" \x3a ' + jsBoolean(canBeNotified) for pluginId, canBeNotified in CanBeNotified.items()]) }
}

/**
 * Variable that will store if the user is an admin that can Accept / Reject bookings
 */
% if UserIsAdmin:
var userIsAdmin = true;
% else:
var userIsAdmin = false;
% endif

/**
 * Stores the load time of the page, expressed in the timezone of the event
 */
var eventLoadTime = IndicoUtil.parseDateTime("${ EventDate }");

/**
 * Stores the load time of the page, expressed in localtime
 */
var clientLoadTime = new Date();

/* ------------------------------ FUNCTIONS TO BE CALLED WHEN USER EVENTS HAPPEN -------------------------------*/

/**
 * Function that will be called when the user presses the "Start" button of a booking.
 * It will call in turn 'startBooking' in Collaboration.js
 */
var start = function(booking) {
    startBooking(booking, '${ Conference.getId() }');
}

/**
 * Function that will be called when the user presses the "Stop" button of a booking.
 * It will call in turn 'stopBooking' in Collaboration.js
 */
var stop = function(booking) {
    stopBooking(booking, '${ Conference.getId() }');
}

var accept = function(booking) {
    acceptBooking(booking, '${ Conference.getId() }');
}

var reject = function(booking) {
    rejectBooking(booking, '${ Conference.getId() }');
}

</script>
