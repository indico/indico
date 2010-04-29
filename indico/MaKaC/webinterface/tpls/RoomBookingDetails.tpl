<% declareTemplate(newTemplateStyle=True) %>
    <script type="text/javascript">
        function submit_cancel()
        {
            if ( !confirm(  <%= _("'Are you sure you want to CANCEL your booking?'")%> ) )
                return;
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingCancelBooking.getURL( reservation ) %>'
            frm.submit()
        }
        function submit_accept()
        {
            if ( !confirm(  <%= _("'Are you sure you want to ACCEPT this booking?'")%> ) )
                return;
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingAcceptBooking.getURL( reservation ) %>'
            frm.submit()
        }
        function submit_reject()
        {
            reason = prompt(  <%= _("'Are you sure you want to REJECT THE _WHOLE_ BOOKING? If so, please give a reason:'")%>, '' );
            if ( reason == null )
                return;
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingRejectBooking.getURL( reservation ) %>' + '&reason=' + encodeURI( reason )
            frm.submit()
        }
        function submit_reject_occurrence( action )
        {
            reason = prompt(  <%= _("'Are you sure you want to REJECT booking for selected date? If so, please give a reason:'")%>, '' );
            if ( reason == null )
                return;
            var frm = document.forms['submits']
            frm.action = action + '&reason=' + encodeURI( reason )
            frm.submit()
        }
        function submit_cancel_occurrence( action )
        {
	    if (confirm('Are you sure you want to remove the selected date from the booking?')) {
	      var frm = document.forms['submits']
              frm.action = action;
              frm.submit();
	    }
        }
        function submit_modify()
        {
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingBookingForm.getURL( reservation ) %>'
            frm.submit()
        }
        function submit_delete()
        {
            if ( !confirm(  <%= _("'THIS ACTION IS IRREVERSIBLE. Are you sure you want to DELETE the booking?'")%> ) )
                return;
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingDeleteBooking.getURL( reservation ) %>'
            frm.submit()
        }
        function submit_clone()
        {
            var frm = document.forms['submits']
            frm.action = '<%= urlHandlers.UHRoomBookingCloneBooking.getURL( reservation ) %>'
            frm.submit()
        }
    </script>

    <!-- CONTEXT HELP DIVS -->
	<div id="tooltipPool" style="display: none">

        <!-- Status -->
		<div id="statusHelp" class="tip">
             <%= _("Validity")%>:<br />
            <ul>
                <li class="tip-no-borders"> <%= _("<b>Not confirmed</b> - the pre-booking is not confirmed (yet) by person responsible.")%></li>
                <li class="tip-no-borders"> <%= _("<b>Cancelled</b> - the booking was cancelled by the requestor himself.")%></li>
                <li class="tip-no-borders"> <%= _("<b>Rejected</b> - the booking was rejected by the person responsible for a room.")%></li>
                <li class="tip-no-borders"> <%= _("<b>Valid</b> - the booking is confirmed and not cancelled. Note that for most rooms bookings are automatically confirmed.")%></li>
            </ul>
             <%= _("Time")%>:<br />
            <ul>
                <li class="tip-no-borders"> <%= _("<b>Live</b> - the booking will take place in the future.")%> </li>
                <li class="tip-no-borders"> <%= _("<b>Archival</b> - the booking already past. It will never repeat in the future.")%></li>
            </ul>
		</div>
        <img style="border-style: solid; border-width: thick; border-color: #101010;" />
        <!-- Repetition type -->
        <div id="repetitionTypeHelp" class="tip">
             <%= _("Repetition type - this indicates how a booking repeats itself.")%>
        </div>
        <!-- Where is key? -->
        <div id="whereIsKeyHelp" class="tip">
             <%= _("How to obtain a key? Often just a phone number.")%>
        </div>
        <!-- Created -->
        <div id="createdHelp" class="tip">
             <%= _("When the booking was made?")%>
        </div>
        <!-- Created -->
        <div id="iWillUseVideoConferencing" class="tip">
             <%= _("Is user going to use video-conferencing equipment?")%><br />
        </div>
        <div id="iNeedAVCSupport" class="tip">
             <%= _("Has user requested support for video-conferencing equipment?")%><br />
        </div>

	</div>

    <!-- END OF CONTEXT HELP DIVS -->

    <table cellpadding="0" cellspacing="0" border="0" width="100%">
		<% if standalone: %>
		    <tr>
		    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
		    </tr>
		<% end %>
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px"><%=bookMessage%>ing</span><br /> <!-- PRE-Booking or Booking -->
                            <% if actionSucceeded: %>
                                <br />
                                <span class="actionSucceeded"><%= title %></span>
                                <p style="margin-left: 6px;"><%= description %></p>
                                <br />
                            <% end %>
                            <br />
                            <table width="90%" align="left" border="0">
                              <!-- ROOM -->
                              <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Room")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><a href="<%= roomDetailsUH.getURL( reservation.room ) %>"><%= reservation.room.name %></a></td>
                                        </tr>
                                        <% if reservation.room.photoId != None: %>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Interior")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="thumbnail"><a href="<%= reservation.room.getPhotoURL() %>" rel="lightbox" title="<%= reservation.room.photoId %>"><img border="1px" src="<%= reservation.room.getSmallPhotoURL() %>"/></a></td>
                                        </tr>
                                        <% end %>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Room key")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.room.whereIsKey %><% contextHelp( 'whereIsKeyHelp' ) %></td>
                                        </tr>
                                    </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- WHEN -->
                              <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("When")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small><%= _("Dates")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= formatDate(reservation.startDT.date()) %> &mdash; <%= formatDate(reservation.endDT.date()) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Hours")%>&nbsp;&nbsp;</small></td>

                                            <td align="left" class="blacktext"><%= verbose_t( reservation.startDT.time() ) %> &mdash; <%= verbose_t( reservation.endDT.time() ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Type")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.verboseRepetition %><% contextHelp( 'repetitionTypeHelp' ) %></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKED FOR -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Booked for")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= verbose( reservation.bookedForName ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("E-mail")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><a style="font-weight: normal" href="mailto:<%= verbose( reservation.contactEmail ) %>"><%= reservation.contactEmail.replace(',',', ') %></a></td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Telephone")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= verbose( reservation.contactPhone ) %></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- CREATED -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Created")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("By")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.verboseCreatedBy %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Date")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= verbose_dt( reservation.createdDT ) %> <% contextHelp( 'createdHelp' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Reason")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.reason %></td>
                                        </tr>
                                        <% if reservation.room.needsAVCSetup: %>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Video-conf.")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <%= verbose( reservation.usesAVC, "no" ) %> <small><font color="grey">(<%= ", ".join(reservation.getUseVC()) %>)</font></small>
                                                <% contextHelp( 'iWillUseVideoConferencing' ) %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Assistance")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <%= verbose( reservation.needsAVCSupport, "no" ) %>
                                                <% contextHelp( 'iNeedAVCSupport' ) %>
                                            </td>
                                        </tr>
                                        <% end %>
                                        <% if reservation.isRejected: %>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Rejection")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.rejectionReason %></td>
                                        </tr>
                                        <% end %>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Status")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= reservation.verboseStatus %><% contextHelp( 'statusHelp' ) %></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Actions")%></span></td>
                                <td>
                                    <form name="submits" action="" method="post">
                                        &nbsp;
                                        <% if reservation.canCancel( user )  and  not reservation.isCancelled and not reservation.isRejected: %>
                                            <input type="button" class="btn" value="<%= _("Cancel Booking")%>" onclick="submit_cancel();return false;"/>
                                        <% end %>
                                        <% if reservation.canReject( user )  and  not reservation.isConfirmed and not reservation.isCancelled and not reservation.isRejected: %>
                                            <input type="button" class="btn" value="<%= _("Accept")%>" onclick="submit_accept();return false;"/>
                                        <% end %>
                                        <% if reservation.canReject( user )  and not reservation.isCancelled and not reservation.isRejected: %>
                                            <input type="button" class="btn" value="<%= _("Reject")%>" onclick="submit_reject();return false;"/>
                                        <% end %>
                                        <% if reservation.canModify( user ): %>
                                            <input type="button" class="btn" value="<%= _("Modify")%>" onclick="submit_modify();return false;"/>
                                        <% end %>
                                        <% if reservation.canDelete( user ): %>
                                            <input type="button" class="btn" value="<%= _("Delete")%>" onclick="submit_delete();return false;"/>
                                        <% end %>
                                        <input type="button" class="btn" value="Clone" onclick="submit_clone();return false;"/>
                                    </form>
                                </td>
                            </tr>
                            <% if reservation.getResvHistory().hasHistory() and ( reservation.isOwnedBy( user ) or reservation.room.isOwnedBy( user ) or user.isAdmin() ) : %>
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKING HISTORY -->
                            <script type="text/javascript">
                                function performSlideOnEntry(entryNum, state){
                                    if ( state ) {
                                         IndicoUI.Effect.slide('bookingEntryLine' + entryNum, eval('height' + entryNum));
                                         $E('bookingEntryMoreInfo' + entryNum).set('More Info');
                                         $E('bookingEntryMoreInfo' + entryNum).dom.className = "fakeLink bookingDisplayEntryMoreInfo";
                                     } else {
                                         IndicoUI.Effect.slide('bookingEntryLine' + entryNum, eval('height' + entryNum));
                                         $E('bookingEntryMoreInfo' + entryNum).set('Hide Info');
                                         $E('bookingEntryMoreInfo' + entryNum).dom.className = "fakeLink bookingDisplayEntryHideInfo";
                                     }
                                     return !state
                                }
                            </script>
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Booking History")%></span></td>
                                <td>
                                <% count = 0 %>
                                <% for entry in reservation.getResvHistory().getEntries() : %>
                                    <% if count == 1 : %>
                                    <!-- Construct the divs needed by the sliding effect -->
                                    <div id="bookingHistoryLine" style="visibility: hidden; overflow: hidden;">
                                    <div class="bookingDisplayBookingHistoryLine">
                                    <% end %>
                                        <div class="bookingHistoryEntry">
                                            <span class="bookingDisplayHistoryTimestamp"><%= entry.getTimestamp() %></span>
                                            <span class="bookingDisplayHistoryInfo"><%= entry.getInfo()[0] %> by <%= entry.getResponsibleUser() %>
                                            <% if len(entry.getInfo()) > 1 : %>
                                                <span class='fakeLink bookingDisplayEntryMoreInfo' id='bookingEntryMoreInfo<%= count %>'> More Info </span>
                                                </span>
                                                <div id="bookingEntryLine<%= count %>"  style="visibility: hidden; overflow: hidden;">
                                                <div class="bookingDisplayEntryLine">
                                                    <ul>
                                                    <% for elem in entry.getInfo(): %>
                                                        <% if entry.getInfo().index(elem) != 0: %>
                                                        <li>
                                                        <%= elem %>
                                                        </li>
                                                        <% end %>
                                                    <% end %>
                                                    </ul>
                                                </div>
                                                </div>
                                                <script type="text/javascript">
                                                    $E('bookingEntryMoreInfo<%= count %>').dom.onmouseover = function (event) {
                                                        IndicoUI.Widgets.Generic.tooltip($E('bookingEntryMoreInfo<%= count %>').dom, event, '<div class="bookingHistoryTooltip">Click here to show / hide detailed information.</div>'
                                                            );
                                                      }
                                                    var showEntryMoreState<%= count %> = false;
                                                    var height<%= count %> = IndicoUI.Effect.prepareForSlide('bookingEntryLine<%= count %>', true);
                                                    $E('bookingEntryMoreInfo<%= count %>').observeClick(function () {
                                                        showEntryMoreState<%= count %> = performSlideOnEntry(<%= count %>, showEntryMoreState<%= count %>);
                                                        });
                                                </script>
                                            <% end %>
                                            <% else : %>
                                                </span>
                                            <% end %>
                                            <% count += 1 %>
                                        </div>
                                <% end %>
                                <% if count > 1 : %>
                                    </div>
                                    </div>
                                    <div class="bookingShowHideHistory">
                                        <span class="fakeLink bookingDisplayShowHistory" id="bookingShowHistory">
                                        Show All History ...
                                        </span>
                                    </div>
                                    <script type="text/javascript">
                                          $E('bookingShowHistory').dom.onmouseover = function (event) {
                                              IndicoUI.Widgets.Generic.tooltip($E('bookingShowHistory').dom, event, '<div class="bookingHistoryTooltip">Click here to show / hide detailed information.</div>'
                                                  );
                                            }
                                          var height = IndicoUI.Effect.prepareForSlide('bookingHistoryLine', true);
                                          var showHistoryState = false;
                                          $E('bookingShowHistory').observeClick(function() {
                                              if (showHistoryState) {
                                                  height = IndicoUI.Effect.prepareForSlide('bookingHistoryLine', false);
                                                  $E('bookingShowHistory').dom.className = "fakeLink bookingDisplayShowHistory";
                                                  IndicoUI.Effect.slide('bookingHistoryLine', height);
                                                  $E('bookingShowHistory').set('Show All History ...');
                                                  }
                                              else {
                                                  $E('bookingShowHistory').dom.className = "fakeLink bookingDisplayHideHistory";
                                                  IndicoUI.Effect.slide('bookingHistoryLine', height);
                                                  $E('bookingShowHistory').set('Hide All History');
                                                  }
                                              showHistoryState = !showHistoryState
                                        });
                                    </script>
                                <% end %>
                                </td>
                            </tr>
                            <% end %>
                            <% if reservation.repeatability != None  and  reservation.getExcludedDays(): %>
                            <tr><td>&nbsp;</td></tr>
                            <!-- Excluded dates -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Excluded days")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                                            <small>
                                                 <%= _("These days are NOT booked.")%>
                                             </small>
                                            </td>
                                            <td align="left" class="excluded" class="blacktext">
                                            <% for day in reservation.getExcludedDays(): %>
                                                <%= formatDate(day) %> <br />
                                            <% end %>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <% end %>
                            <% if reservation.repeatability != None: %>
                            <tr><td>&nbsp;</td></tr>
                            <!-- Occurrences -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> <%= _("Occurrences")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                                            <small>
                                                 <%= _("These days are booked.")%>
                                             </small>
                                            </td>
                                            <td align="left" class="blacktext">
                                            <% canReject = reservation.canReject( user ) %>
                                            <% canCancel = reservation.canCancel( user ) %>

                                            <% for period in reservation.splitToPeriods(): %>
                                                <%= formatDate(period.startDT.date()) %>
                                                <% if canReject: %>
                                                    <a href="javascript: void( 0 )" onclick="submit_reject_occurrence( '<%= urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( reservation, formatDate(period.startDT.date()) ) %>');">Reject</a>
                                                <% end %>
                                                <% if canCancel: %>
                                                    <a href="javascript: void( 0 )" onclick="submit_cancel_occurrence('<%= urlHandlers.UHRoomBookingCancelBookingOccurrence.getURL( reservation, formatDate(period.startDT.date()) ) %>');">Cancel</a>
                                                <% end %>

                                                <br />
                                            <% end %>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <% end %>
                        </table>

                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br />
