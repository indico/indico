    <script type="text/javascript">
        function submit_cancel()
        {
            new ConfirmPopup($T("Cancel booking"),$T("Are you sure you want to CANCEL your booking?"), function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", "${ urlHandlers.UHRoomBookingCancelBooking.getURL(reservation)}");
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_accept()
        {
            new ConfirmPopup($T("Accept booking"),$T("Are you sure you want to ACCEPT your booking?"), function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", "${ urlHandlers.UHRoomBookingAcceptBooking.getURL(reservation)}");
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_reject()
        {
            new ConfirmPopupWithReason($T("Reject booking"),$T("Are you sure you want to REJECT THE _WHOLE_ BOOKING? If so, please give a reason"), function(confirmed) {
                if(confirmed) {
                    var reason = this.reason.get();
                    $("#submits").attr("action", "${ urlHandlers.UHRoomBookingRejectBooking.getURL(reservation)}"+ '&reason=' + encodeURI( reason ));
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();

        }
        function submit_reject_occurrence( action )
        {
            new ConfirmPopupWithReason($T("Reject occurrence"),$T("Are you sure you want to REJECT the booking for the selected date? If so, please give a reason:"), function(confirmed) {
                if(confirmed) {
                    var reason = this.reason.get();
                    $("#submits").attr("action", action + '&reason=' + encodeURI( reason ));
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_cancel_occurrence( action )
        {
            new ConfirmPopup($T("Cancel ocurrence"),$T("Are you sure you want to CANCEL the selected date from the booking?"), function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", action);
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_modify()
        {
            $("#submits").attr("action", "${ modifyBookingUH.getURL(reservation)}");
            $("#submits").submit();
        }
        function submit_delete()
        {
            new ConfirmPopup($T("Delete booking"),$T("THIS ACTION IS IRREVERSIBLE. Are you sure you want to DELETE the booking?"), function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", '${ urlHandlers.UHRoomBookingDeleteBooking.getURL( reservation ) }');
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_clone()
        {
            $("#submits").attr("action", "${cloneURL}");
            $("#submits").submit();
        }
    </script>

    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">

        <!-- Status -->
        <div id="statusHelp" class="tip">
             ${ _("Validity")}:<br />
            <ul>
                <li class="tip-no-borders"> ${ _("<b>Not confirmed</b> - the pre-booking is not confirmed (yet) by person responsible.")}</li>
                <li class="tip-no-borders"> ${ _("<b>Cancelled</b> - the booking was cancelled by the requestor himself.")}</li>
                <li class="tip-no-borders"> ${ _("<b>Rejected</b> - the booking was rejected by the person responsible for a room.")}</li>
                <li class="tip-no-borders"> ${ _("<b>Valid</b> - the booking is confirmed and not cancelled. Note that for most rooms bookings are automatically confirmed.")}</li>
            </ul>
             ${ _("Time")}:<br />
            <ul>
                <li class="tip-no-borders"> ${ _("<b>Live</b> - the booking will take place in the future.")} </li>
                <li class="tip-no-borders"> ${ _("<b>Archival</b> - the booking already past. It will never repeat in the future.")}</li>
            </ul>
        </div>
        <img style="border-style: solid; border-width: thick; border-color: #101010;" />
        <!-- Repetition type -->
        <div id="repetitionTypeHelp" class="tip">
             ${ _("Repetition type - this indicates how a booking repeats itself.")}
        </div>
        <!-- Where is key? -->
        <div id="whereIsKeyHelp" class="tip">
             ${ _("How to obtain a key? Often just a phone number.")}
        </div>
        <!-- Created -->
        <div id="createdHelp" class="tip">
             ${ _("When the booking was made?")}
        </div>
        <!-- Created -->
        <div id="iWillUseVideoConferencing" class="tip">
             ${ _("Is user going to use video-conferencing equipment?")}<br />
        </div>
        <div id="iNeedAVCSupport" class="tip">
             ${ _("Has user requested support for video-conferencing equipment?")}<br />
        </div>

    </div>

    <% canReject = reservation.canReject( user ) %>
    <% canCancel = reservation.canCancel( user ) %>

    <!-- END OF CONTEXT HELP DIVS -->

    <table  style="width: 100%; padding-left: 20px;">
    % if standalone:
        <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
        </tr>
    % endif
        <tr>
            <td>
                <span class="groupTitle bookingTitle" style="padding-top: 0px; border-bottom-width: 0px; font-weight: bold">${ bookMessage }ing</span>
                <!-- PRE-Booking or Booking -->
                % if actionSucceeded:
                    <br />
                    <span class="actionSucceeded">${ title }</span>
                    <p style="margin-left: 6px;">${ description }</p>
                % endif
                <table width="100%" align="left" border="0">
                    <!-- ROOM -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Room")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext"><a href="${ roomDetailsUH.getURL( reservation.room ) }">${ reservation.room.name }</a></td>
                    </tr>
                    % if reservation.room.photoId != None:
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Interior")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="thumbnail"><a href="${ reservation.room.getPhotoURL() }" rel="lightbox" title="${ reservation.room.photoId }"><img border="1px" src="${ reservation.room.getSmallPhotoURL() }"/></a></td>
                    </tr>
                    % endif
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Capacity")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.room.capacity }&nbsp;${_("people")}</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Room key")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.room.whereIsKey }${contextHelp('whereIsKeyHelp' )}</td>
                    </tr>
                    <!-- WHEN -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("When")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top"><small>${ _("Dates")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ formatDate(reservation.startDT.date()) } &mdash; ${ formatDate(reservation.endDT.date()) }</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Hours")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ verbose_t( reservation.startDT.time() ) } &mdash; ${ verbose_t( reservation.endDT.time() ) }</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Type")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.verboseRepetition }${contextHelp('repetitionTypeHelp' )}</td>
                    </tr>
                    <!-- BOOKED FOR -->
                    <tr>
                        <td colspan="2">
                            <div  class="groupTitle bookingTitle">${ _("Booked for")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ verbose( reservation.bookedForName ) }</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("E-mail")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext"><a style="font-weight: normal" href="mailto:${ verbose( reservation.contactEmail ) }">${ reservation.contactEmail.replace(',',', ') }</a></td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Telephone")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ verbose( reservation.contactPhone ) }</td>
                    </tr>
                    <!-- CREATED -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Created")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top"><small> ${ _("By")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.verboseCreatedBy }</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Date")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ verbose_dt( reservation.createdDT ) } ${contextHelp('createdHelp' )}</td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Reason")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.reason }</td>
                    </tr>
                    % if reservation.room.needsAVCSetup:
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Video-conf.")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">
                            ${ verbose( reservation.usesAVC, "no" ) } <small><font color="grey">(${ ", ".join(reservation.getUseVC()) })</font></small>
                            ${contextHelp('iWillUseVideoConferencing' )}
                        </td>
                    </tr>
                    <tr>
                        <td align="right" valign="top" nowrap><small> ${ _("Video-conf Assistance")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">
                            ${ verbose( reservation.needsAVCSupport, "no" ) }
                            ${contextHelp('iNeedAVCSupport' )}
                        </td>
                    </tr>
                    % endif
                    % if rh._isAssistenceEmailSetup and reservation.room.resvNotificationAssistance:
                    <tr>
                        <td align="right" valign="top" nowrap><small> ${ _("Startup Assistance")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ verbose( reservation.needsAssistance, "no" ) }</td>
                    </tr>
                    % endif
                    % if reservation.isRejected:
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Rejection")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.rejectionReason }</td>
                    </tr>
                    % endif
                    <tr>
                        <td align="right" valign="top"><small> ${ _("Status")}&nbsp;&nbsp;</small></td>
                        <td align="left" class="blacktext">${ reservation.verboseStatus }${contextHelp('statusHelp' )}</td>
                    </tr>
                    <!-- ACTIONS -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Actions")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2">
                            <form name="submits" action="" method="post">
                                &nbsp;
                                <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                                    % if canCancel  and  not reservation.isCancelled and not reservation.isRejected:
                                    <li class="button" style="margin-right: 10px" onclick="$('#cancelBooking').click();">
                                        <a href="#">${ _('Cancel Booking')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="cancelBooking" style="display: none;" onclick="submit_cancel();return false;"/>
                                    </li>
                                    % endif
                                    % if canReject  and  not reservation.isConfirmed and not reservation.isCancelled and not reservation.isRejected:
                                    <li class="button" style="margin-right: 10px" onclick="$('#acceptBooking').click();">
                                        <a href="#">${ _('Accept')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="acceptBooking" style="display: none;" onclick="submit_accept();return false;"/>
                                    </li>
                                    % endif
                                    % if canReject  and not reservation.isCancelled and not reservation.isRejected:
                                    <li class="button" style="margin-right: 10px" onclick="$('#rejectBooking').click();">
                                        <a href="#">${ _('Reject')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="rejectBooking" style="display: none;" onclick="submit_reject();return false;"/>
                                    </li>
                                    % endif
                                    % if reservation.canModify( user ):
                                    <li class="button" style="margin-right: 10px" onclick="$('#modifyBooking').click();">
                                        <a href="#">${ _('Modify')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="modifyBooking" style="display: none;" onclick="submit_modify();return false;"/>
                                    </li>
                                    % endif
                                    % if reservation.canDelete( user ):
                                    <li class="button" style="margin-right: 10px" onclick="$('#deleteBooking').click();">
                                        <a href="#">${ _('Delete')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="deleteBooking" style="display: none;" onclick="submit_delete();return false;"/>
                                    </li>
                                    % endif
                                    <li class="button" style="margin-right: 10px" onclick="$('#cloneBooking').click();">
                                        <a href="#">${ _('Clone')}</a>
                                    </li>
                                    <li style="display: none">
                                        <input type="submit" id="cloneBooking" style="display: none;" onclick="submit_clone();return false;"/>
                                    </li>
                                </ul>
                            </form>
                        </td>
                    </tr>
                    % if reservation.getResvHistory().hasHistory() and ( reservation.isOwnedBy( user ) or reservation.room.isOwnedBy( user ) or user.isAdmin() ) :
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
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Booking history")}</div>
                        </td>
                    </tr>
                    <tr>
                       <td>
                        <% count = 0 %>
                        % for entry in reservation.getResvHistory().getEntries() :
                            % if count == 1 :
                            <!-- Construct the divs needed by the sliding effect -->
                            <div id="bookingHistoryLine" style="visibility: hidden; overflow: hidden;">
                            <div class="bookingDisplayBookingHistoryLine">
                            % endif
                                <div class="bookingHistoryEntry">
                                    <span class="bookingDisplayHistoryTimestamp">${ entry.getTimestamp() }</span>
                                    <span class="bookingDisplayHistoryInfo">${ entry.getInfo()[0] } by ${ entry.getResponsibleUser() }
                                    % if len(entry.getInfo()) > 1 :
                                        <span class='fakeLink bookingDisplayEntryMoreInfo' id='bookingEntryMoreInfo${ count }'> More Info </span>
                                        </span>
                                        <div id="bookingEntryLine${ count }"  style="visibility: hidden; overflow: hidden;">
                                        <div class="bookingDisplayEntryLine">
                                            <ul>
                                            % for elem in entry.getInfo():
                                                % if entry.getInfo().index(elem) != 0:
                                                <li>
                                                ${ elem }
                                                </li>
                                                % endif
                                            % endfor
                                            </ul>
                                        </div>
                                        </div>
                                        <script type="text/javascript">
                                            $E('bookingEntryMoreInfo${ count }').dom.onmouseover = function (event) {
                                                IndicoUI.Widgets.Generic.tooltip($E('bookingEntryMoreInfo${ count }').dom, event, '<div class="bookingHistoryTooltip">Click here to show / hide detailed information.</div>'
                                                    );
                                              }
                                            var showEntryMoreState${ count } = false;
                                            var height${ count } = IndicoUI.Effect.prepareForSlide('bookingEntryLine${ count }', true);
                                            $E('bookingEntryMoreInfo${ count }').observeClick(function () {
                                                showEntryMoreState${ count } = performSlideOnEntry(${ count }, showEntryMoreState${ count });
                                                });
                                        </script>
                                    % else :
                                        </span>
                                    % endif
                                    <% count += 1 %>
                                </div>
                        % endfor
                        % if count > 1 :
                            </div>
                            </div>
                            <div class="bookingShowHideHistory">
                                <span class="fakeLink bookingDisplayShowHistory" id="bookingShowHistory">
                                ${ _("Show All History ...")}
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
                        % endif
                        </td>
                    </tr>
                    % endif
                    % if reservation.repeatability != None  and  reservation.getExcludedDays():
                    <!-- Excluded dates -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Excluded days")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                        <small>
                             ${ _("These days are NOT booked.")}
                         </small>
                        </td>
                        <td align="left" class="excluded" class="blacktext">
                        % for day in reservation.getExcludedDays():
                            ${ formatDate(day) } <br />
                        % endfor
                        </td>
                    </tr>
                    % endif
                    % if reservation.repeatability != None:
                    <!-- Occurrences -->
                    <tr>
                        <td colspan="2">
                            <div class="groupTitle bookingTitle">${ _("Occurrences")}</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                        <small>
                             ${ _("These days are booked.")}
                         </small>
                        </td>
                        <td align="left" class="blacktext">

                        % for period in reservation.splitToPeriods():
                            ${ formatDate(period.startDT.date()) }
                            % if canReject:
                                <a href="javascript: void( 0 )" onclick="submit_reject_occurrence( '${ urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( reservation, formatDate(period.startDT.date()) ) }');">Reject</a>
                            % endif
                            % if canCancel:
                                <a href="javascript: void( 0 )" onclick="submit_cancel_occurrence('${ urlHandlers.UHRoomBookingCancelBookingOccurrence.getURL( reservation, formatDate(period.startDT.date()) ) }');">Cancel</a>
                            % endif

                            <br />
                        % endfor
                        </td>
                    </tr>
                    % endif
                    % if (reservation.room.isOwnedBy( user ) or user.isRBAdmin()) and not reservation.isConfirmed and collisions:
                        <!-- Occurrences -->
                        <tr>
                            <td>
                                <div class="groupTitle bookingTitle">${ _("Occurrences")}</div>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                % for col in collisions:
                                    <strong>${"PRE-" if not col.withReservation.isConfirmed else ""}Booking: </strong>${ col.withReservation.bookedForName }, ${ verbose_dt(col.withReservation.startDT) } - ${ verbose_dt(col.withReservation.endDT) }
                                    (<a href="${ urlHandlers.UHRoomBookingBookingDetails.getURL(col.withReservation) }" target="_blank">${ _("show this booking") }</a>)<br/>
                                % endfor
                            </td>
                        </tr>
                    % endif
                </table>
            </td>
         </tr>
      </table>
    <br />
