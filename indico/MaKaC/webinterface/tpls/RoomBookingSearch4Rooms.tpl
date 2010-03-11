
<script type="text/javascript">

    // Displays div with dates and hours
    function display_availability( bool)
    {
        trs = $( 'sdatesTR', 'edatesTR', 'hoursTR', 'repTypeTR', 'includePrebookingsTR' )
        for ( i = 0; i < trs.length; i++ )
        {
            if ( bool ) trs[i].style.display = ''      // Show
            if ( !bool ) trs[i].style.display = 'none' // Hide
        }
    }
    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid( onSubmit )
    {
        if ( onSubmit != true )
            onSubmit = false;

        // Clean up - make all textboxes white again
        f1 = $('searchForm')
        period_clean_redouts( f1 )
        f1.capacity.className = ''

        // Init
        isValid = true

        // Simple search -------------------------------------
        // Availability
        if ( !$('searchForm').availability[2].checked ) // only if NOT "Don't care"
        {
            isValid = validate_period( f1 )
        }
        // capacity
        if ( $F( 'capacity' ).length > 0 && parseInt( $F( 'capacity' ), 10 ).toString() == 'NaN' )
        {
            f1.capacity.className = 'invalid'
            isValid = false
        }

        // Holidays warning
        if ( isValid && !onSubmit )
        {
            new Ajax.Updater(
                'holidays-warning',
                '<%= urlHandlers.UHRoomBookingGetDateWarning.getURL() %>',
                { parameters: $(f1).serialize(true) }
            );
        }

        if (f1.sdate.value == '' ){
              f1.sdate.className = 'invalid'
              isValid = false;
           }

        if (f1.edate.value == ''){
              f1.edate.className = 'invalid'
              isValid = false;
           }

        return isValid
    }
    // Check whether a room can be booked (or pre-booked) by the user
    // If not, pop up a dialog
    function isBookable()
    {
        // Get the selected option in the SELECT
        var selectedURL = $F('roomName');
        var roomLocationPattern = /roomLocation=([a-zA-Z0-9\-]*)(?:&|$)/;
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
                                "You\'re not allowed to book this room");
                        popup.open();
                    }
                } else {
                    bookButtonWrapper.set(bookButton);
                    IndicoUtil.errorReport(error);
                }
            });
    }

</script>

        <!-- CONTEXT HELP DIVS -->
	    <div id="tooltipPool" style="display: none">
            <!-- Choose Button -->
            <div id="chooseButtonHelp" class="tip">
                <span>Black</span> -  <%= _("rooms that <b>does not</b> require confirmation")%><br />
                <span class="moderatedRoom">Orange</span> -  <%= _("rooms that <b>require confirmation")%></b><br />
                <span class="privateRoom">Red</span> -  <%= _("rooms not publically bookable")%><br />
            </div>
            <!-- Free Search -->
            <div id="freeSearchHelp" class="tip">
                 <%= _("Type in anything you remember about the room, i.e.")%>:
                <ul>
                    <li class="tip-no-borders"> <%= _("building or room number")%></li>
                    <li class="tip-no-borders"> <%= _("person responsible")%></li>
                    <li class="tip-no-borders"> <%= _("part of comment")%></li>
                    <li class="tip-no-borders"> <%= _("equipment")%></li>
                    <li class="tip-no-borders"> <%= _("room site")%></li>
                    <li class="tip-no-borders"> <%= _("telephone")%></li>
                    <li class="tip-no-borders">...</li>
                </ul>
                 <%= _("Results will include rooms that have at least one of the specified words somewhere in description.") %>
                <br />
                 <%= _("Examples") %>:
                <ul>
                    <li class="tip-no-borders">Hauser &nbsp; ( <%= _("name of person responsible")%>)</li>
                    <li class="tip-no-borders">513- 31- 28- &nbsp; (buildings)</li>
                    <li class="tip-no-borders">-006 -C19  &nbsp; (rooms)</li>
                    <li class="tip-no-borders">prevessin &nbsp; (site)</li>
                </ul>
                 <%= _("Searching is case-insensitive and concerns all room's attributes.")%>
            </div>
            <!-- Capacity -->
            <div id="capacityHelp" class="tip">
            <p class="tip-no-borders">
                <!--<span style="width: 30px; background-color: Red">&nbsp;</span><span style="width: 80px; background-color: Lime">&nbsp;</span><span style="width: 80px; background-color: Green">&nbsp;</span>!<br />
                -->
                 <%= _("""Find only rooms having capacity within 20%% range.
                In example for capacity = 20, rooms having capacity 16 - 24
                will be included in searching results.""")%><br />
            </p>
            <p class="tip-no-borders">
                 <%= _("""If there are no rooms of capacity within 20%% range,
                system will search for greater capacity.""")%>
            </p>
            <p class="tip-no-borders">
                 <%= _("""Example: for capacity equal 1, system will try to find rooms for
                only one person. This of course fails, so it will
                return rooms with capacity greater than 1.""")%>
            </p>
            </div>
            <!-- Availability -->
            <div id="availabilityHelp" class="tip">
                <ul>
                    <li class="tip-no-borders"> <%= _("Available - the room must be available in the <b>whole</b> period")%></li>
                    <li class="tip-no-borders"> <%= _("Booked - the room must be booked <b>any time</b> in the period")%></li>
                    <li class="tip-no-borders"> <%= _("Don't care - room's availability is not checked")%></li>
                </ul>
            </div>
            <% includeTpl( 'CHBookingRepeatition' ) %>
        </div>
        <!-- END OF CONTEXT HELP DIVS -->


		<table cellpadding="0" cellspacing="0" border="0" width="80%%">
		<% if standalone: %>
		    <tr>
		    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%%">&nbsp;</td> <!-- lastvtabtitle -->
		    </tr>
		<% end %>
        <tr>
		<td class="bottomvtab" width="100%%">
		    <!-- Main cell -->
			<table width="100%%" cellpadding="0" cellspacing="0" class="htab" border="0">
				<tr>
					<td class="maincell">
						<p><span class="formTitle" style="border-bottom-width: 0px"> <%= _("Search for a room")%></span></p>
						<!-- Background table (adds image) -->
						<table width="100%%" class="ACtab">
						    <tr>
						        <td>
						            <!-- First section -->
						            <table width="90%%" align="center" border="0">
                                        <tr>
                                            <td colspan="2" class="groupTitle"><%= _("Choose a room")%></td>
                                        </tr>
                                        <tr>
                                        <td nowrap="nowrap" class="titleCellTD"><span class="titleCellFormat"> <%= _("Room")%></span></td>
                                        <td width="80%%">
                                            <form id="chooseForm" method="post">
                                                <select name="roomName" id="roomName">
                                                <% for room in rooms: %>
                                                  <% selected = "" %>
                                                  <% if room.name == eventRoomName: %>
                                                    <% selected = 'selected="selected"' %>
                                                  <% end %>
                                                  <% url = detailsUH.getURL( room ) %>
                                                  <% if forNewBooking: %>
                                                      <% url = bookingFormUH.getURL( room ) %>
                                                  <% end %>
                                                  <option value="<%= url %>" <%= selected %> class="<%=roomClass( room )%>"><%= room.locationName + ": &nbsp; " + room.getFullName() %></option>
                                                <% end %>
                                                </select>

                                                <% if forNewBooking: %>
                                                    <span id="bookButtonWrapper"><input id="bookButton" class="btn" type="button" value="<%= _("Book")%>" onclick="isBookable();" /></span>
                                                <% end %>
                                                <% if not forNewBooking: %>
                                                    <input class="btn" type="button" value="<%= _("Room details")%>" onclick="document.location = $F( 'roomName' ); return false;" />
                                                <% end %>

                                                <!-- Help -->
                                                <% contextHelp( 'chooseButtonHelp' ) %>
                                            </form>
                                        </td>
                                        </tr>
                                    </table>
                                    <br />
                                    <form id="searchForm" method="post" action="<%= roomBookingRoomListURL %>">
                                    <table width="90%%" align="center" border="0">
                                        <tr>
                                            <td colspan="2" class="groupTitle"><%= _("Search for a room") %></td>
                                        </tr>
                                        <!-- LOCATION (PLUGIN) -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Location")%></span></td>
                                            <td>
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> <%= _("Location")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <select name="roomLocation" id="roomLocation">
                                                                <option value=""><%= Location.getDefaultLocation().friendlyName %></option>
												                <% for loc in Location.allLocations: %>
                                                                    <% if loc.friendlyName != Location.getDefaultLocation().friendlyName: %>
                                                                        <option value="<%=loc.friendlyName%>" ><%= loc.friendlyName %></option>
                                                                    <% end %>
												                <% end %>
                                                            </select>
                                                            <!-- HACK to make form submitable with ENTER. This is just submit button copied and hidden. -->
                                                            <input style="width: 0px; position:absolute; left: -50px;" type="submit" class="btn" onclick="if (!forms_are_valid( true )) { alert(  <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; };" value="" />
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- FREE TEXT -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Room description")%></span></td>
                                            <td>
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> <%= _("Must contain")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="freeSearch" size="30" type="text" name="freeSearch" />
                                                            <% contextHelp( 'freeSearchHelp' ) %>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- AVAILABILITY -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Availability")%></span></td>
                                            <td >
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right" ><small> <%= _("Must be")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input name="availability" type="radio" value="Available" onclick="display_availability( true ); " <% if forNewBooking: %>checked="checked"<%%> /> <%= _("Available")%>
                                                            <input name="availability" type="radio" value="Booked" onclick="display_availability( true ); "/> <%= _("Booked")%>
                                                            <input name="availability" type="radio" value="Don't care" onclick="display_availability( false )" <% if not forNewBooking: %>checked="checked"<%%>/> <%= _("Don't care")%>
                                                            <% contextHelp( 'availabilityHelp' ) %>
                                                        </td>
                                                    </tr>
                                                    <% includeTpl( 'RoomBookingPeriodForm', form = 1 ) %>
                                                    <tr id='includePrebookingsTR'>
                                                        <td class="subFieldWidth" align="right" ><small> <%= _("PRE-Bookings")%></small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="includePrebookings" name="includePrebookings" type="checkbox" checked="checked"/>
                                                             <%= _("Check conflicts against pre-bookings")%>
                                                            <% inlineContextHelp(  _("[v] Check if you want to avoid conflicts with PRE-bookings. By default conflicts are checked only against confirmed bookings.") ) %>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- CAPACITY -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Capacity")%></span></td>
                                            <td align="right">
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td class="subFieldWidth" align="right"><small> <%= _("About")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="3" type="text" id="capacity" name="capacity"/>  <%= _("people")%>
                                                            <% contextHelp( 'capacityHelp' ) %>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- REQUIRED EQUIPMENT -->
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Required equipment")%></td>
                                            <td align="right">
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td width="80px" align="right" valign="top"><small> <%= _("I need...")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <% for eq in possibleEquipment: %>
                                                                <input id="<%= "equ_" + eq %>" name="<%= "equ_" + eq %>" type="checkbox"><%= eq %></input><br />
                                                            <% end %>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Special attributes")%></td>                                    <td align="right">
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td width="80px" align="right" valign="top"><small> <%= _("Is public")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isReservable" name="isReservable" type="checkbox" checked="checked"/>
                                                            <% inlineContextHelp(  _("[v] Include only publically reservable rooms.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="80px" align="right" valign="top"><small> <%= _("Auto confirm")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="isAutoConfirmed" name="isAutoConfirmed" type="checkbox"/>
                                                            <% inlineContextHelp(  _("[v] Include only rooms, where bookings are automatically confirmed. This is the case for most rooms.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <% if user.isResponsibleForRooms(): %>
                                                        <tr>
                                                            <td width="80px" align="right" valign="top"><small> <%= _("Only mine")%>&nbsp;&nbsp;</small></td>
                                                            <td align="left" class="blacktext">
                                                                <input id="onlyMy" name="onlyMy" type="checkbox" />
                                                                <% inlineContextHelp(  _("[v] Include only rooms you are responsible for.") ) %>
                                                                <br />
                                                            </td>
                                                        </tr>
                                                    <% end %>
                                                    <% if user.isAdmin(): %>
                                                        <tr>
                                                            <td width="80px" align="right" valign="top"><small> <%= _("Active?")%>&nbsp;&nbsp;</small></td>
                                                            <td align="left" class="blacktext">
                                                                <input id="isActive" name="isActive" type="checkbox" checked="checked"/>
                                                                <% inlineContextHelp(  _("[v] Include only active rooms. <b>This should be checked.</b> Please note that inactive rooms are considered deleted.") ) %>
                                                                <br />
                                                            </td>
                                                        </tr>
                                                    <% end %>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-left:20px"><input type="submit" class="btn" onclick="if (!forms_are_valid( true )) {alert(  <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; };" value="<%= _('Search') %>" /></td></tr>
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
        <!-- Just to initialize -->
        <script type="text/javascript">
            Event.observe( window, 'load',
                function () {
                    if ( forms_are_valid() )
                        set_repeatition_comment();
                    if ( $('searchForm').availability[2].checked ) // if "Don't care" about availability
                        display_availability( false );
                    $( 'freeSearch' ).focus();
                    new Form.Observer( 'searchForm', 0.4, forms_are_valid );
                }
            );
        </script>
