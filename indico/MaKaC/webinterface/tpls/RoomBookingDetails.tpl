    <script type="text/javascript">
        function createContentDiv(title, occurs) {
            var content = $("<div/>", {css: {maxWidth: '400px', textAlign: 'left'}});
            content.append(title);
            if (occurs) {
                var occursdiv = $("<div/>", {css: {
                    maxHeight: '80px',
                    marginTop:'10px',
                    marginBottom: '10px',
                    overflow: 'auto',
                    listStylePosition: 'inside',
                    textAlign: 'left'
                }});
                occursdiv.append($T("This applies to all the following ocurrences ({0} in total):".format(occurs.length)));
                occursdiv.addClass("warningMessage");
                var occurslist = $("<ul/>")
                for(var i=0; i<occurs.length; i++) {
                    occurslist.append($('<li/>').text(occurs[i]));
                }
                occursdiv.append(occurslist)
                content.append(occursdiv);
            }
            return content.get(0);
        }

        function submit_cancel(occurs) {
            contentDiv = createContentDiv($T("Are you sure you want to <strong>cancel the whole booking</strong>?"), occurs);
            new ConfirmPopup($T("Cancel booking"), contentDiv, function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", "${ urlHandlers.UHRoomBookingCancelBooking.getURL(reservation)}");
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_accept() {
            new ConfirmPopup($T("Accept booking"), $T("Are you sure you want to <strong>accept</strong> this booking?"), function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", "${ urlHandlers.UHRoomBookingAcceptBooking.getURL(reservation)}");
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_reject(occurs) {
            contentDiv = createContentDiv($T("Are you sure you want to <strong>reject the whole booking</strong>?"), occurs);
            new ConfirmPopupWithReason($T("Reject booking"), contentDiv, function(confirmed) {
                if(confirmed) {
                    var reason = this.reason.get();
                    $("#submits").attr("action", build_url("${ urlHandlers.UHRoomBookingRejectBooking.getURL(reservation)}", {reason: reason}));
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();

        }
        function submit_reject_occurrence(action, date) {
            contentDiv = createContentDiv($T("Are you sure you want to <strong>reject</strong> the booking for the selected date") + " (" + date + ")?");
            new ConfirmPopupWithReason($T("Reject occurrence"), contentDiv, function(confirmed) {
                if(confirmed) {
                    var reason = this.reason.get();
                    $("#submits").attr("action", build_url(action, {reason: reason}));
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_cancel_occurrence(action, date) {
            contentDiv = createContentDiv($T("Are you sure you want to <strong>cancel</strong> the booking for the selected date") + " (" + date + ")?");
            new ConfirmPopup($T("Cancel ocurrence"), contentDiv, function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", action);
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_modify() {
            $("#submits").attr("action", "${ modifyBookingUH.getURL(reservation)}");
            $("#submits").submit();
        }
        function submit_delete() {
            contentDiv = createContentDiv($T("This action is irreversible. Are you sure you want to <strong>delete</strong> the booking?"));
            new ConfirmPopup($T("Delete booking"), contentDiv, function(confirmed) {
                if(confirmed) {
                    $("#submits").attr("action", '${ urlHandlers.UHRoomBookingDeleteBooking.getURL( reservation ) }');
                    $("#submits").submit();
                }
            }, $T("Yes"), $T("No")).open();
        }
        function submit_clone() {
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

    <table cellpadding="0" cellspacing="0" border="0" width="100%">
        % if standalone:
            <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
            </tr>
        % endif
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">${bookMessage} (${ reservation.room.name })</span><br /> <!-- PRE-Booking or Booking -->

                            <!-- Action result message-->
                            % if actionSucceeded:
                                <p class="successMessage">${ title } <br/> ${ description }</p>
                            % endif

                            <!-- Warning for pre-bookings -->
                            % if isPreBooking and not actionSucceeded:
                                <p class="warningMessage">${ _("Please note that this is a") } <b>${ _("pre-booking") }</b>. ${_("This means that you shouldn't use the room unless you receive the confirmation that it has been accepted.") }</p>
                            % endif

                            <table width="90%" align="left" border="0">
                              <!-- ROOM -->
                              <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Room")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Name")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext"><a href="${ roomDetailsUH.getURL( reservation.room ) }">${ reservation.room.name }</a></td>
                                        </tr>
                                        % if reservation.room.photoId != None:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Interior")}&nbsp;&nbsp;</td>
                                            <td align="left" class="thumbnail"><a href="${ reservation.room.getPhotoURL() }" nofollow="lightbox" title="${ reservation.room.photoId }"><img border="1px" src="${ reservation.room.getSmallPhotoURL() }"/></a></td>
                                        </tr>
                                        % endif
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Capacity")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.room.capacity }&nbsp;${_("people")}</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Room key")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.room.whereIsKey }${contextHelp('whereIsKeyHelp' )}</td>
                                        </tr>
                                    </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- WHEN -->
                              <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("When")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Dates")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ formatDate(reservation.startDT.date()) } &mdash; ${ formatDate(reservation.endDT.date()) }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Hours")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose_t( reservation.startDT.time() ) } &mdash; ${ verbose_t( reservation.endDT.time() ) }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Type")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.verboseRepetition }${contextHelp('repetitionTypeHelp' )}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKED FOR -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Booked for")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Name")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose( reservation.bookedForName ) }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("E-mail")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext"><a style="font-weight: normal" href="mailto:${ verbose( reservation.contactEmail ) }">${ reservation.contactEmail.replace(',',', ') }</a></td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Telephone")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose( reservation.contactPhone ) }</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- CREATED -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Created")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("By")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.verboseCreatedBy }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Date")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose_dt( reservation.createdDT ) } ${contextHelp('createdHelp' )}</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Reason")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.reason }</td>
                                        </tr>
                                        % if reservation.room.needsAVCSetup:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Video-conf.")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                ${ verbose( reservation.usesAVC, "no" ) } <font color="grey">(${ ", ".join(reservation.getUseVC()) })</font>
                                                ${contextHelp('iWillUseVideoConferencing' )}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" nowrap> ${ _("Video-conf Assistance")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                ${ verbose( reservation.needsAVCSupport, "no" ) }
                                                ${contextHelp('iNeedAVCSupport' )}
                                            </td>
                                        </tr>
                                        % endif
                                        % if rh._isAssistenceEmailSetup and reservation.room.resvNotificationAssistance:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" nowrap>${ _("Startup Assistance")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                ${ verbose( reservation.needsAssistance, "no" ) }
                                            </td>
                                        </tr>
                                        % endif
                                        % if reservation.isRejected:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Rejection")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.rejectionReason }</td>
                                        </tr>
                                        % endif
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Status")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ reservation.verboseStatus }${contextHelp('statusHelp' )}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Actions")}</span></td>
                                <td>
                                    <form id="submits" name="submits" action="" method="post">
                                        <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left; padding-top: 15px">
                                        % if not reservation.isCancelled and not reservation.isRejected:
                                            % if canCancel:
                                                <li class="button" style="margin-left: 10px" onclick="submit_cancel(${[str(formatDate(period.startDT.date(), format='d MMM yyyy')) for period in reservation.splitToPeriods()]});return false;">
                                                    <a href="#" onClick="return false;">${ _("Cancel Booking")}</a>
                                                </li>
                                            % endif
                                            % if canReject and not reservation.isConfirmed:
                                                <li class="button" style="margin-left: 10px" onclick="submit_accept();return false; return false;">
                                                    <a href="#" onClick="return false;">${ _("Accept")}</a>
                                                </li>
                                            % endif
                                            % if canReject:
                                                <li class="button" style="margin-left: 10px" onclick="submit_reject(${[str(formatDate(period.startDT.date(), format='d MMM yyyy')) for period in reservation.splitToPeriods()]});return false;">
                                                    <a href="#" onClick="return false;">${ _("Reject")}</a>
                                                </li>
                                            % endif
                                            % if reservation.canModify(user):
                                                <li class="button" style="margin-left: 10px" onclick="submit_modify();return false;">
                                                    <a href="#" onClick="return false;">${ _("Modify")}</a>
                                                </li>
                                            % endif
                                        % endif
                                        % if reservation.canDelete(user):
                                            <li class="button" style="margin-left: 10px" onclick="submit_delete();return false;">
                                                <a href="#" onClick="return false;">${ _("Delete")}</a>
                                            </li>
                                        % endif
                                        <li class="button" style="margin-left: 10px" onclick="submit_clone();return false;">
                                            <a href="#" onClick="return false;">${ _("Clone")}</a>
                                        </li>
                                        <li style="display: none"></li>
                                        </ul>
                                    </form>
                                </td>
                            </tr>
                            % if reservation.getResvHistory().hasHistory() and ( reservation.isOwnedBy( user ) or reservation.room.isOwnedBy( user ) or user.isAdmin() ) :
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKING HISTORY -->
                            <script type="text/javascript">
                                function performSlideOnEntry(entryNum, state) {
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
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Booking History")}</span></td>
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
                                % endif
                                </td>
                            </tr>
                            % endif
                            % if reservation.repeatability != None  and  reservation.getExcludedDays():
                            <tr><td>&nbsp;</td></tr>
                            <!-- Excluded dates -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Excluded days")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                                                 ${ _("These days are NOT booked.")}
                                            </td>
                                            <td align="left" class="excluded" class="blacktext">
                                            % for day in reservation.getExcludedDays():
                                                ${ formatDate(day) } <br />
                                            % endfor
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            % endif
                            % if reservation.repeatability != None:
                            <tr><td>&nbsp;</td></tr>
                            <!-- Occurrences -->
                            <tr>
                                <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Occurrences")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                                                 ${ _("These days are booked.")}
                                            </td>
                                            <td align="left" class="blacktext">

                                            % for period in reservation.splitToPeriods():
                                                ${ formatDate(period.startDT.date()) }
                                                % if not reservation.isCancelled and not reservation.isRejected:
                                                    % if canReject:
                                                        <a class="roomBookingRejectOccurrence" href="#" onclick="submit_reject_occurrence('${urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL(reservation, date=formatDate(period.startDT.date(), format='yyyy-M-d'))}', '${formatDate(period.startDT.date(), format='d MMM yyyy')}');return false;">Reject</a>
                                                    % endif
                                                    % if canCancel:
                                                        <a class="roomBookingCancelOccurrence" href="#" onclick="submit_cancel_occurrence('${urlHandlers.UHRoomBookingCancelBookingOccurrence.getURL(reservation, date=formatDate(period.startDT.date(), format='yyyy-M-d'))}', '${formatDate(period.startDT.date(), format='d MMM yyyy')}');return false;">Cancel</a>
                                                    % endif
                                                % endif
                                                <br />
                                            % endfor
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            % endif
                            % if (reservation.room.isOwnedBy( user ) or user.isRBAdmin()) and not reservation.isConfirmed and collisions:
                                <tr><td>&nbsp;</td></tr>
                                <!-- Occurrences -->
                                <tr>
                                    <td class="bookingDisplayTitleCell"><span class="titleCellFormat"> ${ _("Conflicts at the same time")}</span></td>
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
            </td>
        </tr>
    </table>
    <br />
