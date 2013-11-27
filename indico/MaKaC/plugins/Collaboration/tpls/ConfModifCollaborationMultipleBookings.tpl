<table>
    <tr>
        <td colspan="2" style="padding-top: 20px"></td>
    </tr>
    <tr>
        <td class="titleCellNoBorderTD" style="white-space: nowrap;vertical-align: middle;">
            <span class="titleCellFormat createBookingText">
                ${ _("Create booking")}
            </span>
        </td>
        <td style="padding-left: 15px;">
            <% plugins = MultipleBookingPlugins %>
            <select id="pluginSelect" onchange="pluginSelectChanged()">
                <option value="noneSelected">-- Choose a system --</option>
                % for p in plugins:
                    <option value="${p.getId()}">${ p.getName() }</option>
                % endfor
            </select>
            <div style="display: inline;">
                <input id="createBooking" type="button" value="${_('Create')}"/>
                <input id="searchBooking" type="button" style="display:none" value="${_('Search')}"/>
            </div>
        </td>
    </tr>
</table>
<table>
    <tr>
        <td class="group_title" style="display: block; padding:10px 0px 0px;" colspan="2">
            ${ _("Current bookings")}
            <div class="toolbar right">
              <div class="group" style="font-size:13px; padding:0">
                <a id="startAll" class="i-button icon-play highlight hidden" onclick="startAll()">${ _("Start All")}</a>
                <a id="stopAll" class="i-button icon-stop highlight hidden" onclick="stopAll()">${ _("Stop All")}</a>
              </div>
            </div>
        </td>
    </tr>
    <tr>
        <td colspan="2">
            <table style="border-collapse: collapse;">
                <thead>
                    <tr id="tableHeadRow" style="margin-bottom: 5px;">
                        <td></td>
                    </tr>
                </thead>
                <tbody id="bookingsTableBody">
                    <tr><td></td></tr>
                </tbody>
            </table>
        </td>
    </tr>
</table>

<script type="text/javascript">


/* ------------------------------ GLOBAL VARIABLES ------------------------------- */

// HTML code for the popup dialog that will appear when adding or editing a booking, depending on the booking type
var forms = {
${ ",\n". join(['"' + pluginName + '" \x3a ["' + escapeHTMLForJS(newBookingForm) + '", "' + escapeHTMLForJS(advancedTabForm) + '"]' for pluginName, (newBookingForm, advancedTabForm) in MultipleBookingForms.items()]) }
}

/**
  * Watchlist of bookings objects, pickled from Indico CSBooking objects.
  * Structure of a booking object:
  * id: the id of the booking. Examples: 1,3,10,12
  * type: the plugin / booking type that this booking belongs to. Examples: EVO, DummyPlugin
  * statusMessage: a string representing the current status of the booking. Examples: "Booking accepted", "Booking refused"
  * statusClass: the CSS class for the status message.
  * bookingParams: an object / dictionary with plugin-defined parameters that are need to perform a booking.
  * startParams: an object / dictionary with plugin-defined parameters that may be needed to execute a local (browser, opposed to server)
  *              start action, such as downloading koala.jnlp with some given parameters, or sending a command to a Tandberg camera.
  * Different flags that depend on the plugin to which the booking belongs to, but are present in all booking objects for convenience:
  *     -hasStart : true if the plugin has a "start" concept. Otherwise, the "start" button will not appear, etc.
  *     -hasStop : true if the plugin has a "stop" concept. Otherwise, the "stop" button will not appear, etc.
  *     -hasConnect : true if the plugin has a "connect" concept. Otherwise, the "connect" button will not appear, etc.
  *     -hasDisconnect : true if the plugin has a "disconnect" concept. Otherwise, the "disconnect" button will not appear, etc.
  *     -requiresServerCallForStart: true if we should notify the server when the user presses the "start" button.
  *     -requiresServerCallForStop: true if we should notify the server when the user presses the "stop" button.
[  *     -requiresClientCallForStart: true if the browser should execute some JS action when the user presses the "start" button.
  *     -requiresClientCallForStop: true if the browser should execute some JS action when the user presses the "stop" button.
  * Other flags that depend on the booking object:
  *     -canBeStarted : If its value is true, the "start" button for the booking will be able to be pushed.
  *                     It can be false if, for example:
  *                           + The server didn't like the booking parameters and doesn't give permission for the booking to be started,
  *                           + The booking has already been started, so the "start" button has to be faded in order not to be pressed twice.
  *     -canBeStopped: If its value is true, the "stop" button for the booking will be able to be pushed.
  *                    For example, before starting a booking the "stop" button for the booking will be faded.
  *     -permissionToStart : Even if the "start" button for a booking is able to be pushed, there may be cases where the booking should
  *                          not start. For example, if it's not the correct time yet.
  *                          In that case "permissionToStart" should be set to false so that the booking doesn't start.
  *     -permissionToStop: Same as permissionToStart. Sometimes the booking should not be allowed to stop even if the "stop" button is available.
  */

var bookings = $L(${ jsonEncode(BookingsM) });

var hasCreatePermissions = ${ jsonEncode(HasCreatePermissions) };
var videoServiceSupport = ${ jsonEncode(VideoServiceSupport) };
var isAllowedToSearch = ${ jsonEncode(isAllowedToSearch) };

var confId = ${ Conference.getId() };

/* ------------------------------ UTILITY / HELPER FUNCTIONS -------------------------------*/

/**
 * Returns a String with the name of the plugin currently selected in the 'pluginSelect' select widget.
 * Example: EVO, DummyPlugin...
 * @return {String}
 */
var getSelectedPlugin = function() {
    value = $E('pluginSelect').dom.value;
    return value == 'noneSelected' ? null : value;
}

var pluginSelectChanged = function() {
    selectedPlugin = getSelectedPlugin();
    if (exists(selectedPlugin)) {
        if (isAllowedToSearch[selectedPlugin]) {
            $('#searchBooking').show();
        }  else {
            $('#searchBooking').hide();
        }
        $('#createBooking').disabledButtonWithTooltip('enable');
    } else {
        $('#searchBooking').hide();
        $('#createBooking').disabledButtonWithTooltip('disable');
    }
}

/* ------------------------------ FUNCTIONS TO BE CALLED WHEN USER EVENTS HAPPEN -------------------------------*/

/**
 * Function that will be called when the user presses the "Remove" button for a plugin.
 * It will call in turn 'removeBooking' in Collaboration.js
 */
var remove = function(booking) {
    removeBooking(booking, '${ Conference.getId() }');
};


/**
 * Function that will be called when the user presses the "Edit" button of a booking.
 * It will call in turn 'editBooking' in Collaboration.js
 */
var edit = function(booking) {
    editBooking(booking, '${ Conference.getId() }');
};

/* ------------------------------ STUFF THAT HAPPENS WHEN PAGE IS LOADED -------------------------------*/

$(function(){
    // This is strictly necessary in this page because the progress dialog touches the body element of the page,
    // and IE doesn't like when this is done at page load by a script that is not inside the body element.

    // We configure the buttons and the list of plugins.

    $('#createBooking').on('click', function() {
        selectedPlugin = getSelectedPlugin();
        if (exists(selectedPlugin)) {
            createBooking(selectedPlugin, '${ Conference.getId() }');
        }
    });

    $('#searchBooking').on('click', function() {
        searchBookings(selectedPlugin, '${ Conference.getId() }');
    });

    $('#createBooking').disabledButtonWithTooltip({
        disabled: true,
        tooltip: $T('Please select a booking type from the list.')
    });

    $("#pluginSelect").qtip({
        content: {
            text: $T('Select a booking type from the drop-down list and press the "Create" or "Search" button.')
        },
        hide: {
            fixed: true
        }
    });

    $E('pluginSelect').dom.value = 'noneSelected';
    pluginSelectChanged();

    // We display the bookings
    displayBookings();
});

% if MultipleBookingPlugins:
$(function(){
    % for plugin in MultipleBookingPlugins:
    if (pluginHasFunction("${plugin.getName()}", "onLoad")) {
        codes["${plugin.getName()}"]["onLoad"]();
    }
    % endfor
});
% endif
</script>
