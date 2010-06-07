<% declareTemplate(newTemplateStyle=True) %>
<script type="text/javascript">
    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid( onSubmit )
    {
        if ( onSubmit != true )
            onSubmit = false;

        // Init, clean up (make all textboxes white again)
        var f1 = $('bookingForm')
        period_clean_redouts( f1 )
        f1.bookedForName.className = f1.contactEmail.className = f1.contactPhone.className = f1.reason.className = ''

        var isValid = true
        isValid = validate_period( f1, true, <%= allowPast %>  ) && isValid
        isValid = required_fields( ['bookedForName', 'contactEmail', 'reason'] ) && isValid

        if ( !valid_email( $F( 'contactEmail' ) ) )
        {
            isValid = false
            $('contactEmail').className = 'invalid'
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

	<% if candResv.room.needsAVCSetup: %>

	$('vcSystemList').className=''

	if ($('usesAVC').checked) {

  	  var oneChecked = false;

	  $$('input.videoConferenceOption').each(function(elem){
	    if (elem.checked)
	    {
	      oneChecked = true;
	    }
	  });

	  if (!oneChecked) {
	    $( 'vcSystemList' ).className = 'invalid';
	    isValid = false;
	  }

	}
	<% end %>


        return isValid;
    }

    function submit_booking()
    {
        $('bookingForm').action = "<%= saveBookingUH.getURL( conf ) %>"
        $('bookingForm').submit()
    }




</script>

    <!-- CONTEXT HELP DIVS -->
	<div id="tooltipPool" style="display: none">
        <!-- Where is key? -->
        <div id="whereIsKeyHelp" class="tip">
             <%= _("How to obtain a key? Often just a phone number.")%>
        </div>
        <div id="skipConflictsHelp" class="tip">
             <%= _("Creates or saves your booking only for available dates. All conflicting days will be excluded.")%>
        </div>
        <div id="iWillUseVideoConferencing" class="tip">
             <%= _("Check <b>if</b> you are going to use video-conferencing equipment.")%><br />
        </div>
        <div id="iNeedAVCSupport" class="tip">
             <%= _("Check <b>if</b> you need AVC Support to help you with video-conferencing equipment.")%><br />
        </div>
        <% includeTpl( 'CHBookingRepeatition' ) %>
    </div>
    <!-- END OF CONTEXT HELP DIVS -->

    <form id="bookingForm" action="#conflicts" method="post">
    <input type="hidden" id="afterCalPreview" name="afterCalPreview" value="True" />
    <table cellpadding="0" cellspacing="0" border="0" width="80%%">
		<% if standalone: %>
		    <tr>
		    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%%">&nbsp;</td> <!-- lastvtabtitle -->
		    </tr>
		<% end %>
        <tr>
            <td class="bottomvtab" width="100%%">
                <table width="100%%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">
                            <input type="hidden" name="roomID" id="roomID" value="<%=candResv.room.id%>" />
                            <input type="hidden" name="roomLocation" id="roomLocation" value="<%=candResv.room.locationName%>" />
                            <% if formMode == FormMode.NEW: %>
                                 <%= _("New")%> <%=bookingMessage%>ing
                            <% end %>
                            <% if formMode == FormMode.MODIF: %>
                                 <%= _("Modify")%> <%=bookingMessage%>ing
                                <input type="hidden" name="resvID" id="resvID" value="<%=candResv.id%>" />
                            <% end %>
                            </span><br />
                            <% if showErrors: %>
                                <br /><a href="#conflicts" style="color: Red; margin-left: 6px;"> <%= _("Saving failed. Please review details below.")%></a><br /><br />
                            <% end %>
                            <br />
                            <table width="100%%" align="left" border="0">
                              <% includeTpl( "RoomBookingRoomMiniDetails", room = candResv.room ) %>
                              <tr><td>&nbsp;</td></tr>
                              <!-- WHEN -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("When")%></span></td>
                                <td>
                                    <table width="100%%">
                                        <% includeTpl( "RoomBookingPeriodForm", repeatability = candResv.repeatability, form = 0, unavailableDates = candResv.room.getNonBookableDates() ) %>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKED FOR -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Booked for")%></span></td>
                                <td>
                                    <table width="100%%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="text" id="bookedForName" name="bookedForName" style="width: 240px;" value="<%= verbose( candResv.bookedForName ) %>" />
                                                <% inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("E-mail")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="text" id="contactEmail" name="contactEmail" style="width: 240px;" value="<%= verbose( candResv.contactEmail )%>" />
                                                <% inlineContextHelp( '<b>Required.</b> Contact email.' ) %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" class="subFieldWidth" valign="top"><small> <%= _("Telephone")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="text" id="contactPhone" name="contactPhone" style="width: 240px;" value="<%= verbose( candResv.contactPhone ) %>" />
                                                <% inlineContextHelp( 'Contact telephone.' ) %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" class="subFieldWidth" valign="top"><small> <%= _("Reason")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <textarea rows="3" cols="50" id="reason" name="reason" ><%= verbose( candResv.reason ) %></textarea>
                                                <% inlineContextHelp( _("<b>Required.</b> The justification for booking. Why do you need this room?")) %>
                                            </td>
                                        </tr>
                                        <% if candResv.room.needsAVCSetup: %>
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="top"><small><span style="color: Red;"><%= _("I will use video-conf. equipment (please check only what you need)")%></span>&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input id="usesAVC" name="usesAVC" type="checkbox" <% if candResv.usesAVC: %> checked="checked" <% end%> />
                                                    <% contextHelp( 'iWillUseVideoConferencing' ) %>


                                                </td>
                                            </tr>
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="middle"><small><span style="color: Red;">I will use video-conf. system</span>&nbsp;&nbsp;</small></td>
                                                <td align="left" id="vcSystemList" class="blacktext">
                                                    <% for vc in candResv.room.getAvailableVC(): %>
                                                        <% checked = "" %>
                                                        <% if vc in candResv.getUseVC(): %>
                                                            <% checked = """checked="checked" """ %>
                                                        <% end %>
                                                        <%= """<br>\n<input id="vc_%s" name="vc_%s" class="videoConferenceOption" type="checkbox" onclick="if(this.checked){$(usesAVC).checked=true;}" %s /> %s"""%(vc[:3], vc[:3], checked, vc) %>
                                                    <% end %>
                                                    <br><br>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="top"><small><span style="color: Red;"> <%= _("I need assistance")%></span>&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input id="needsAVCSupport" name="needsAVCSupport" type="checkbox" <% if candResv.needsAVCSupport: %> checked="checked" <%end%> onclick="if ( this.checked ) { $( 'usesAVC' ).checked = true; }" />
                                                    <% contextHelp( 'iNeedAVCSupport' ) %>
                                                </td>
                                            </tr>
                                        <% end %>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Actions")%></span></td>
                                <td>
	                               	<input type="hidden" name="conf" value="<%= conf %>" />
									<input type="hidden" name="standalone" value="<%= standalone %>" />
	                               	<input type="submit" class="btn" value="<%= _("Re-check for conflicts")%>" onclick="if (!validate_period(document.forms[0], true, <%= allowPast %>)) { alert( <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); return false; }"/>
	                               	<input type="submit" class="btn"  <% if formMode==FormMode.MODIF: %> value="Save" <%%> value="<%= bookingMessage %>" onclick="if (forms_are_valid( true )) { submit_booking(); } else { alert( <%= _("'There are errors in the form. Please correct fields with red background.'")%> ); }; return false;" />
                                    (
                                    <input type="checkbox" name="skipConflicting" id="skipConflicting" <% if skipConflicting: %> checked="checked" <%%> />
                                     <%= _("skip conflicting dates")%>
                                    <% contextHelp( 'skipConflictsHelp' ) %>
                                    )
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <a name="conflicts"></a>
                                    <%= roomBookingRoomCalendar %>
                                </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                </table>

            </td>
        </tr>
    </table>
    </form>
    <br />
    <!-- Just to initialize -->
    <script type="text/javascript">
        Event.observe( window, 'load',
            function ()
            {
                if ( forms_are_valid() )
                    set_repeatition_comment();
                new Form.Observer( 'bookingForm', 0.4, forms_are_valid );
            }
        );
        <% if candResv.room.needsAVCSetup: %>
            alert("The conference room you have chosen is equiped\\nfor video-conferencing and video-projection.\\nIf you need this equipment, DO NOT FORGET to select it.\\nIf you don't need any of this equipment please choose\\nanother room, if a suitable one is free on a suitable\\nlocation for your meeting.\\n\\n\\n                    Thank you for your understanding.")
        <% end %>

    </script>
