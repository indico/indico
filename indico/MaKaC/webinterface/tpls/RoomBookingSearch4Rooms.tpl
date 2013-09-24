
<script type="text/javascript">

    // Displays div with dates and hours
    function display_availability(bool) {
        $('#sdatesTR, #edatesTR, #hoursTR, #repTypeTR, #includePrebookingsTR, #includePendingBlockingsTR').toggle(bool);
    }
    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid(onSubmit) {
        if (onSubmit != true) {
            onSubmit = false;
        }

        // Clean up - make all textboxes white again
        var searchForm = $('#searchForm');
        $(':input', searchForm).removeClass('invalid');
        // Init
        var isValid = true;

        // Simple search -------------------------------------
        // Availability
        if (!$('input[name="availability"]', searchForm).is(':checked')) { // only if NOT "Don't care"
            isValid = validate_period();
        }
        // capacity
        if ($('#capacity').val().length > 0 && parseInt($('#capacity').val(), 10).toString() == 'NaN') {
            $('#capacity').addClass('invalid');
            isValid = false;
        }

        // Holidays warning
        if (isValid && !onSubmit) {
            var lastDateInfo = searchForm.data('lastDateInfo');
            var dateInfo = $('#sDay, #sMonth, #sYear, #eDay, #eMonth, #eYear').serialize();
            if (dateInfo != lastDateInfo) {
                searchForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource('roomBooking.getDateWarning', searchForm.serializeObject());

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $E('holidays-warning').set(holidaysWarning.get());
                    }
                });
            }
        }

        if (!$('#sdate').val()) {
            $('#sdate').addClass('invalid');
            isValid = false;
        }

        if (!$('#edate').val()) {
            $('#edate').addClass('invalid');
            isValid = false;
        }

        return isValid;
    }
    // Check whether a room can be booked (or pre-booked) by the user
    // If not, pop up a dialog
    function isBookable() {
        // Get the selected option in the SELECT
        var selectedURL = $('#roomName').val();
        var roomLocationPattern = /roomLocation=([a-zA-Z0-9\-\+]*)(?:&|$)/;
        var roomIDPattern = /roomID=([a-zA-Z0-9\-]*)(?:&|$)/;

        // Get the room location and id from the url
        var roomLocation = selectedURL.match(roomLocationPattern);
        var roomID = selectedURL.match(roomIDPattern);

        var bookButton = $E("bookButton");
        var bookButtonWrapper = $E("bookButtonWrapper");
        bookButtonWrapper.set(progressIndicator(true, false));

        // Send an asynchronous request to the server
        // Depending of result, either redirect to the
        // Room Booking form or pop up a dialog
        indicoRequest('user.canBook',
            {roomLocation: roomLocation[1], roomID: roomID[1]},
            function(result, error) {
                if(!error) {
                    if (result) {
                        document.location = selectedURL;
                    } else {
                        bookButtonWrapper.set(bookButton);
                        var popup = new AlertPopup('Booking Not Allowed',
                                "You're not allowed to book this room");
                        popup.open();
                    }
                } else {
                    bookButtonWrapper.set(bookButton);
                    IndicoUtil.errorReport(error);
                }
            });
    }

    $(window).on('load', function() {
        $('#searchForm').delegate(':input', 'keyup change', function() {
            forms_are_valid();
        }).submit(function(e) {
            if (!forms_are_valid(true)) {
                e.preventDefault();
                new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
            };
        });

        if (forms_are_valid()) {
            set_repeatition_comment();
        }
        if ($('#searchForm input[name="availability"]').is(':checked')) { // if "Don't care" about availability
            display_availability(false);
        }
        $('#searchForm input[name="availability"]').change(function() {
            display_availability($(this).data('showAvailability'));
        });
        display_availability($('input[name=availability]:checked').data('showAvailability'));
        $('#freeSearch').focus();
    });


</script>

        <!-- CONTEXT HELP DIVS -->
        <div id="tooltipPool" style="display: none">
            <!-- Choose Button -->
            <div id="chooseButtonHelp" class="tip">
                <span>Black</span> -  ${ _("rooms that <b>do not</b> require confirmation")}<br />
                <span class="moderatedRoom">Orange</span> -  ${ _("rooms that <b>require confirmation")}</b><br />
                <span class="privateRoom">Red</span> -  ${ _("rooms not publically bookable")}<br />
            </div>
            <!-- Free Search -->
            <div id="freeSearchHelp" class="tip">
                 ${ _("Type in anything you remember about the room, i.e.")}:
                <ul>
                    <li class="tip-no-borders"> ${ _("building or room number")}</li>
                    <li class="tip-no-borders"> ${ _("person responsible")}</li>
                    <li class="tip-no-borders"> ${ _("part of comment")}</li>
                    <li class="tip-no-borders"> ${ _("equipment")}</li>
                    <li class="tip-no-borders"> ${ _("room site")}</li>
                    <li class="tip-no-borders"> ${ _("telephone")}</li>
                    <li class="tip-no-borders">...</li>
                </ul>
                 ${ _("Results will include rooms that have at least one of the specified words somewhere in description.") }
                <br />
                 ${ _("Examples") }:
                <ul>
                    <li class="tip-no-borders">Hauser &nbsp; ( ${ _("name of person responsible")})</li>
                    <li class="tip-no-borders">513- 31- 28- &nbsp; (buildings)</li>
                    <li class="tip-no-borders">-006 -C19  &nbsp; (rooms)</li>
                    <li class="tip-no-borders">prevessin &nbsp; (site)</li>
                </ul>
                 ${ _("Searching is case-insensitive and concerns all room's attributes.")}
            </div>
            <!-- Capacity -->
            <div id="capacityHelp" class="tip">
            <p class="tip-no-borders">
                <!--<span style="width: 30px; background-color: Red">&nbsp;</span><span style="width: 80px; background-color: Lime">&nbsp;</span><span style="width: 80px; background-color: Green">&nbsp;</span>!<br />
                -->
                 ${ _("""Find only rooms having capacity within 20% range.
                In example for capacity = 20, rooms having capacity 16 - 24
                will be included in searching results.""")}<br />
            </p>
            <p class="tip-no-borders">
                 ${ _("""If there are no rooms of capacity within 20% range,
                system will search for greater capacity.""")}
            </p>
            <p class="tip-no-borders">
                 ${ _("""Example: for capacity equal 1, system will try to find rooms for
                only one person. This of course fails, so it will
                return rooms with capacity greater than 1.""")}
            </p>
            </div>
            <!-- Availability -->
            <div id="availabilityHelp" class="tip">
                <ul>
                    <li class="tip-no-borders"> ${ _("Available - the room must be available in the <b>whole</b> period")}</li>
                    <li class="tip-no-borders"> ${ _("Booked - the room must be booked <b>any time</b> in the period")}</li>
                    <li class="tip-no-borders"> ${ _("Don't care - room's availability is not checked")}</li>
                </ul>
            </div>
            <%include file="CHBookingRepeatition.tpl"/>
        </div>
        <!-- END OF CONTEXT HELP DIVS -->


        <table cellpadding="0" cellspacing="0" border="0" width="80%">
        % if standalone:
            <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
            </tr>
        % endif
        <tr>
        <td class="bottomvtab" width="100%">
            <!-- Main cell -->
            <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                <tr>
                    <td class="maincell">
                        <h2 class="page_title">
                            ${ _("Search rooms")}
                        </h2>
                        <!-- Background table (adds image) -->
                        <table width="100%" class="ACtab">
                            <tr>
                                <td>
                                    <!-- First section -->
                                    <table width="90%" align="center" border="0">
                                        <tr>
                                            <td colspan="2">
                                                <h2 class="group_title">
                                                    ${_("Choose a room")}
                                                </h2>
                                            </td>
                                        </tr>
                                        <tr>
                                        <td nowrap="nowrap" class="titleCellTD"><span class="titleCellFormat"> ${ _("Room")}</span></td>
                                        <td width="80%">
                                            <form id="chooseForm" method="post">
                                                <select name="roomName" id="roomName">
                                                % for room in rooms:
                                                  <% selected = "" %>
                                                  % if room.name == eventRoomName:
                                                    <% selected = 'selected="selected"' %>
                                                  % endif
                                                  <% url = detailsUH.getURL( room ) %>
                                                  % if forNewBooking:
                                                      <% url = bookingFormUH.getURL( room ) %>
                                                  % endif
                                                  <option value="${ url }" ${ selected } class="${roomClass( room )}">${ room.locationName + ": &nbsp; " + room.getFullName() }</option>
                                                % endfor
                                                </select>

                                                % if forNewBooking:
                                                    <span id="bookButtonWrapper"><input id="bookButton" class="btn" type="button" value="${_("Book")}" onclick="isBookable();" /></span>
                                                % endif
                                                % if not forNewBooking:
                                                    <input class="btn" type="button" value="${ _("Room details")}" onclick="document.location = $('#roomName').val(); return false;" />
                                                % endif

                                                <!-- Help -->
                                                ${contextHelp('chooseButtonHelp' )}
                                            </form>
                                        </td>
                                        </tr>
                                    </table>
                                    <br />
                                    <form id="searchForm" method="post" action="${ roomBookingRoomListURL }">
                                    <table width="90%" align="center" border="0">
                                        <tr>
                                            <td colspan="2">
                                                <h2 class="group_title">
                                                    ${_("Search for a room")}
                                                </h2>
                                            </td>
                                        </tr>
                                        <!-- LOCATION (PLUGIN) -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Location")}</span></td>
                                            <td>
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> ${ _("Location")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <select name="roomLocation" id="roomLocation">
                                                                % if Location.getDefaultLocation():
                                                                <option value="">${ Location.getDefaultLocation().friendlyName }</option>
                                                                % endif
                                                                % for loc in Location.allLocations:
                                                                    % if Location.getDefaultLocation() and loc.friendlyName != Location.getDefaultLocation().friendlyName:
                                                                        <option value="${loc.friendlyName}" >${ loc.friendlyName }</option>
                                                                    % endif
                                                                % endfor
                                                            </select>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- FREE TEXT -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Room description")}</span></td>
                                            <td>
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> ${ _("Must contain")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="freeSearch" size="30" type="text" name="freeSearch" />
                                                            ${contextHelp('freeSearchHelp' )}
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- AVAILABILITY -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Availability")}</span></td>
                                            <td >
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> ${ _("Must be")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input name="availability" type="radio" value="Available" data-show-availability="true" ${'checked="checked"' if forNewBooking else ""} /> ${ _("Available")}
                                                            <input name="availability" type="radio" value="Booked" data-show-availability="true" /> ${ _("Booked")}
                                                            <input name="availability" type="radio" value="Don't care" data-show-availability="false" ${'checked="checked"' if not forNewBooking else ""}/> ${ _("Don't care")}
                                                            ${contextHelp('availabilityHelp' )}
                                                        </td>
                                                    </tr>
                                                    <%include file="RoomBookingPeriodFormOld.tpl" args="form = 1, unavailableDates = [], availableDayPeriods = [] "/>
                                                    <tr id='includePrebookingsTR'>
                                                        <td class="subFieldWidth" align="right" ><small> ${ _("PRE-Bookings")}</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="includePrebookings" name="includePrebookings" type="checkbox" checked="checked"/>
                                                             ${ _("Check conflicts against pre-bookings")}
                                                            ${inlineContextHelp(_("[v] Check if you want to avoid conflicts with PRE-bookings. By default conflicts are checked only against confirmed bookings.") )}
                                                        </td>
                                                    </tr>
                                                    <tr id='includePendingBlockingsTR'>
                                                        <td class="subFieldWidth" align="right" ><small> ${ _("Blockings")}</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="includePendingBlockings" name="includePendingBlockings" type="checkbox" checked="checked"/>
                                                             ${ _("Check conflicts against pending blockings")}
                                                            ${inlineContextHelp(_("[v] Check if you want to avoid conflicts with pending blockings. By default conflicts are checked only against confirmed blockings.") )}
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- CAPACITY -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Capacity")}</span></td>
                                            <td align="right">
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right"><small> ${ _("About")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="3" type="text" id="capacity" name="capacity"/>  ${ _("people")}
                                                            ${contextHelp('capacityHelp' )}
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- REQUIRED EQUIPMENT -->
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Required equipment")}</td>
                                            <td align="right">
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" valign="top">${ _("I need...")}&nbsp;&nbsp;</td>
                                                        <td align="left" class="blacktext" >
                                                            % for eq in possibleEquipment:
                                                                <input id="${ "equ_" + eq }" name="${ "equ_" + eq }" type="checkbox">${ eq }</input><br />
                                                            % endfor
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Special attributes")}</td>
                                            <td align="right">
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" valign="top">${ _("Is public")}&nbsp;&nbsp;</td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isReservable" name="isReservable" type="checkbox" checked="checked"/>
                                                            ${inlineContextHelp(_("[v] Include only publically reservable rooms.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" valign="top">${ _("Auto confirm")}&nbsp;&nbsp;</td>
                                                        <td align="left" class="blacktext">
                                                            <input id="isAutoConfirmed" name="isAutoConfirmed" type="checkbox"/>
                                                            ${inlineContextHelp(_("[v] Include only rooms, where bookings are automatically confirmed. This is the case for most rooms.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    % if isResponsibleForRooms:
                                                        <tr>
                                                            <td class="subFieldWidth" align="right" valign="top">${ _("Only mine")}&nbsp;&nbsp;</td>
                                                            <td align="left" class="blacktext">
                                                                <input id="onlyMy" name="onlyMy" type="checkbox" />
                                                                ${inlineContextHelp(_("[v] Include only rooms you are responsible for.") )}
                                                                <br />
                                                            </td>
                                                        </tr>
                                                    % endif
                                                    % if user.isAdmin():
                                                        <tr>
                                                            <td class="subFieldWidth" align="right" valign="top">${ _("Active?")}&nbsp;&nbsp;</td>
                                                            <td align="left" class="blacktext">
                                                                <input id="isActive" name="isActive" type="checkbox" checked="checked"/>
                                                                ${inlineContextHelp(_("[v] Include only active rooms. <b>This should be checked.</b> Please note that inactive rooms are considered deleted.") )}
                                                                <br />
                                                            </td>
                                                        </tr>
                                                    % endif
                                                </table>
                                            </td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-left:20px"><input type="submit" class="btn" value="${ _('Search') }" /></td></tr>
                                    </table>
                                    </form>
                                    <br />
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                </table>
            </td>
        </tr>
        </table>
