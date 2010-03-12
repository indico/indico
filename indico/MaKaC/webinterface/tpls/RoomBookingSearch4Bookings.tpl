<% calendarIconURL = Config.getInstance().getSystemIconURL("calendar") %>

<script type="text/javascript">

    // Displays div with dates and hours
	function period_clean_redouts( f1 )
	{
        f1.sDay.className = f1.sMonth.className = f1.sYear.className = f1.sdate.className = ''
        f1.eDay.className = f1.eMonth.className = f1.eYear.className = f1.edate.className = ''
        f1.sTime.className = f1.eTime.className = ''
    }
    function all_date_fields_are_blank()
    {
        return $F('sDay')=='' && $F('sMonth')=='' && $F('sYear')=='' && $F('sdate')=='' && $F('eDay')=='' && $F('eMonth')=='' && $F('eYear')=='' && $F('edate')==''
    }
    function all_time_fields_are_blank()
    {
        return $F( 'sTime' ) == '' && $F( 'eTime' ) == ''
    }

    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid( onSubmit )
    {
        if ( onSubmit != true )
            onSubmit = false;

        // Clean up - make all textboxes white again
        var f1 = $('searchForm')
        period_clean_redouts( f1 )

        // Init
        isValid = true

        // Simple search
        if ( !all_date_fields_are_blank() )
            isValid = validate_period( f1, false, true, 1 ) // 1: validate only dates
        if ( !all_time_fields_are_blank() )
            isValid = isValid && validate_period( f1, false, true, 2 ) // 2: validate only times

        // Holidays warning
        if ( isValid && !onSubmit )
        {
            new Ajax.Updater(
                'holidays-warning',
                '<%= urlHandlers.UHRoomBookingGetDateWarning.getURL() %>',
                { parameters: $(f1).serialize(true) }
            );
        }

        return isValid
    }

    function confirm_search()
    {
        if ( $F('onlyMy') )
            return true;
        if ( $F('roomGUID')[0] != undefined  &&  $F('roomGUID')[0].length > 0 )
            return true;
        try { if ( $F('ofMyRooms') ) return true; } catch (err) {}
        /*c = confirm( 'It is recommended to click "Cancel" and choose a room. Your query is very generic and it may take long time to process. Are you sure you want to continue?' )
        if ( c )
        {
            $( 'submitBtn1' ).disabled = true;
            $( 'submitBtn2' ).disabled = true;
        }*/
        alert( 'Please select a room (or several rooms).' )
        return false;
    }

    IndicoUI.executeOnLoad(function()
    {

        var startDate = IndicoUI.Widgets.Generic.dateField_sdate(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField_edate(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);


        /* In case the date changes, we need to check whether the start date is greater than the end date,
        and if it's so we need to change it */
        startDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                endDate.set(startDate.get());
                endDate.dom.onchange();
            }
        });

        endDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                startDate.set(endDate.get());
                startDate.dom.onchange();
            }
        });

       <% if today.day != '': %>
            startDate.set('<%= today.day %>/<%= today.month %>/<%= today.year %>');
        <% end %>

        <% if weekLater.day != '': %>
            endDate.set('<%= weekLater.day %>/<%= weekLater.month %>/<%= weekLater.year %>');
        <% end %>

     });
</script>
        <!-- CONTEXT HELP DIVS -->
	    <div id="tooltipPool" style="display: none">
            <!-- Choose Button -->
            <div id="chooseButtonHelp" class="tip">
                Directly choose the room.
            </div>
<!--            ## includeTpl( 'CHBookingRepeatition' ) ##-->
        </div>
        <!-- END OF CONTEXT HELP DIVS -->

		<table cellpadding="0" cellspacing="0" border="0" width="80%%">
	    <tr>
	    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%%">&nbsp;</td> <!-- lastvtabtitle -->
	    </tr>
        <tr>
		<td class="bottomvtab" width="100%%">
		    <!-- Main cell -->
			<table width="100%%" cellpadding="0" cellspacing="0" class="htab" border="0">
				<tr>
					<td class="maincell">
						<p><span class="formTitle" style="border-bottom-width: 0px"> <%= _("Search for bookings")%></span></p>
						<!-- Background table (adds image) -->
						<table width="100%%" class="ACtab">
						    <tr>
						        <td>
                                    <form id="searchForm" method="post" action="<%= roomBookingBookingListURL %>">
                                    <table width="90%%" align="center" border="0" style="border-left: 1px solid #777777;">
                                        <tr>
                                            <td colspan="2" class="groupTitle"> <%= _("Simple Search")%></td>
                                        </tr>
                                        <!-- For room -->
                                        <tr>
                                            <td nowrap="nowrap" class="titleCellTD"><span class="titleCellFormat"> <%= _("Room")%></span></td>
                                            <td width="80%%">
                                                <table width="100%%">
                                                <tr>
                                                    <td class="subFieldWidthSmaller" align="right" ><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                                    <td align="left" class="blacktext">
                                                        <select name="roomGUID" id="roomGUID" multiple="multiple" size="8">
                                                            <option value="allRooms"> All Rooms</option>
											                <% for room in rooms: %>
                                                                <option value="<%= str( room.guid ) %>" class="<%= roomClass( room ) %>"><%= room.locationName + " &nbsp; " + room.getFullName() %></option>
											                <% end %>
                                                        </select>
                                                        <% inlineContextHelp( _("You can select multiple rooms the same way you select multiple files in Windows - press (and hold) left mouse button and move the cursor. Alternatively you can use keyboard - hold SHIFT and press up/down arrows.") ) %>
														<input type="hidden" name="search" value="on" />
                                                        <!-- HACK to make form submitable with ENTER. This is just submit button copied and hidden. -->
                                                        <input style="width: 0px; position:absolute; left: -50px;" type="submit" class="btn" onclick="if (!forms_are_valid( true )) { alert(  <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; }; return confirm_search();" value="<%= _('Search') %>" />
                                                    </td>
                                                </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr >
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Spans over")%></span></td>
                                            <td>
                                                <table width="100%%">

                                                <tr id="sdatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> <%= _("Start Date")%>&nbsp;&nbsp;</small></td>
                                            <td class="blacktext">
                                                <span id="sDatePlace"></span>
                                                <input type="hidden" value="<%= today.day %>" name="sDay" id="sDay" onchange="this.form.eDay.value=this.value;"/>
                                                <input type="hidden" value="<%= today.month %>" name="sMonth" id="sMonth" onchange="this.form.eMonth.value=this.value;"/>
                                                <input type="hidden" value="<%= today.year %>" name="sYear" id="sYear" onchange="this.form.eYear.value=this.value;"/>
                                            </td>
                                          </tr>
                                         <tr id="edatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> <%= _("End Date")%>&nbsp;&nbsp;</small></td>
                                            <td>
                                                <span id="eDatePlace"></span>
                                                <input type="hidden" value="<%= weekLater.day %>" name="eDay" id="eDay"/>
                                                <input type="hidden" value="<%= weekLater.month %>" name="eMonth" id="eMonth"/>
                                                <input type="hidden" value="<%= weekLater.year %>" name="eYear" id="eYear"/>
                                            </td>
                                        </tr>


                                                <tr id="hoursTR" >
                                                    <td align="right" ><small> <%= _("Hours")%>&nbsp;&nbsp;</small></td>
                                                    <td align="left" class="blacktext">
                                                        <input name="sTime" id="sTime" maxlength="5" size="5" type="text" value="" /> &nbsp;&mdash;&nbsp;
                                                        <input name="eTime" id="eTime" maxlength="5" size="5" type="text" value="" />
                                                        <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
                                                    </td>
                                                </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- Booked for -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Booked for")%></span></td>
                                            <td align="right">
                                                <table width="100%%">
                                                    <tr>
                                                        <td class="subFieldWidthSmaller" align="right"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="30" type="text" id="bookedForName" name="bookedForName" />
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- Reason -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Reason")%></span></td>
                                            <td align="right">
                                                <table width="100%%">
                                                    <tr>
                                                        <td class="subFieldWidthSmaller" align="right"><small> <%= _("Reason")%>&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="30" type="text" id="reason" name="reason" />
                                                        </td>
                                                    </tr>
                                                </table>
                                                <input id="submitBtn1" type="submit" class="btn" onclick="if (!forms_are_valid( true )) { alert(  <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; }; return confirm_search();" value="<%= _('Search') %>" />
                                            </td>
                                        </tr>
                                    </table>
                                    <br>
                                    <table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
                                        <tr>
                                            <td colspan="2" class="groupTitle"> <%= _("Advanced search")%></td>
                                        </tr>
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> <%= _("Attributes")%></td>
                                            <td align="right">
                                                <table width="100%%" cellspacing="4px">
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Only Bookings&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyBookings" name="onlyBookings" type="checkbox" onchange="javascript: if (this.checked) { $('onlyPrebookings').checked = false; }"/>
                                                            <% inlineContextHelp( _("[v] Show only <b>Bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Only Pre-bookings&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyPrebookings" name="onlyPrebookings" type="checkbox" onchange="javascript: if (this.checked) { $('onlyBookings').checked = false; }" />
                                                            <% inlineContextHelp( _("[v] Show only <b>PRE-bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Only mine&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyMy" name="onlyMy" type="checkbox" />
                                                            <% inlineContextHelp( '[v] Show only <b>your</b> bookings.' ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <% if user.isResponsibleForRooms(): %>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Of my rooms&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="ofMyRooms" name="ofMyRooms" type="checkbox" />
                                                            <% inlineContextHelp(  _("[v] Only bookings of rooms you are responsible for.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <% end %>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Is rejected&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isRejected" name="isRejected" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Is cancelled&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isCancelled" name="isCancelled" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Is archival&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isArchival" name="isArchival" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Uses video-conf.&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="usesAVC" name="usesAVC" type="checkbox" />
                                                            <% inlineContextHelp( '[v] Show only bookings which will use video conferencing systems.' ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Require Video-conf. support&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="needsAVCSupport" name="needsAVCSupport" type="checkbox" />
                                                            <% inlineContextHelp( '[v] Show only bookings which require video conferencing support.' ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td width="165px" align="right" valign="top"><small>Is heavy&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isHeavy" name="isHeavy" type="checkbox" />
                                                            <% inlineContextHelp(  _("[v] Show only <b>heavy</b> bookings.") ) %>
                                                            <br />
                                                        </td>
                                                    </tr>
                                                </table>
                                                <input id="submitBtn2" type="submit" class="btn" onclick="if (!forms_are_valid( true )) { alert( <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; }; return confirm_search();" value="<%= _("Search")%>" />
                                            </td>
                                        </tr>
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
                function() { new Form.Observer( 'searchForm', 0.4, forms_are_valid ); }
            );
        </script>
