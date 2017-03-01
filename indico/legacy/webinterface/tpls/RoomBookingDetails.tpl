<% valid_occurrences = reservation.occurrences.filter_by(is_valid=True).all() %>
<% import itertools %>
<% from indico.modules.rb.util import rb_is_admin %>

<script type="text/javascript">
    var occurrences = ${ [formatDate(occ.date) for occ in valid_occurrences] | n,j };
    function createContentDiv(title, occurs) {
        var content = $("<div/>", {css: {maxWidth: '400px', textAlign: 'left'}});
        content.append(title);
        if (occurs && occurrences.length) {
            var occursdiv = $("<div>", {
                css: {
                    maxHeight: '100px',
                    marginTop:'10px',
                    marginBottom: '10px',
                    overflow: 'auto',
                    listStylePosition: 'inside',
                    textAlign: 'left'
                }
            });
            occursdiv.append($T("This applies to all the following occurrences ({0} in total):".format(occurrences.length)));
            occursdiv.addClass("warningMessage");
            var occurslist = $("<ul/>");
            for(var i = 0; i < occurrences.length; i++) {
                occurslist.append($('<li>').text(occurrences[i]));
            }
            occursdiv.append(occurslist);
            content.append(occursdiv);
        }
        return content.get(0);
    }

    function submit_cancel(occurs) {
        var contentDiv = createContentDiv($T("Are you sure you want to <strong>cancel the whole booking</strong>?"), true);
        new ConfirmPopup($T("Cancel booking"), contentDiv, function(confirmed) {
            if(confirmed) {
                $("#reason").val('');
                $("#submits").attr("action", "${ url_for(endpoints['booking_cancel'], reservation, event) }");
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();
    }
    function submit_accept() {
        new ConfirmPopup($T("Accept booking"), $T("Are you sure you want to <strong>accept</strong> this booking?"), function(confirmed) {
            if(confirmed) {
                $("#reason").val('');
                $("#submits").attr("action", "${ url_for(endpoints['booking_accept'], reservation, event) }");
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();
    }
    function submit_reject() {
        var contentDiv = createContentDiv($T("Are you sure you want to <strong>reject the whole booking</strong>?"), true);
        new ConfirmPopupWithReason($T("Reject booking"), contentDiv, function(confirmed) {
            if(confirmed) {
                var reason = this.reason.get();
                $("#reason").val(reason);
                $("#submits").attr("action", "${ url_for(endpoints['booking_reject'], reservation, event) }");
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();

    }
    function submit_reject_occurrence(action, date) {
        var contentDiv = createContentDiv($T("Are you sure you want to <strong>reject</strong> the booking for the selected date") + " (" + date + ")?");
        new ConfirmPopupWithReason($T("Reject occurrence"), contentDiv, function(confirmed) {
            if(confirmed) {
                var reason = this.reason.get();
                $("#reason").val(reason);
                $("#submits").attr("action", action);
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();
    }
    function submit_cancel_occurrence(action, date) {
        var contentDiv = createContentDiv($T("Are you sure you want to <strong>cancel</strong> the booking for the selected date") + " (" + date + ")?");
        new ConfirmPopup($T("Cancel occurrence"), contentDiv, function(confirmed) {
            if(confirmed) {
                $("#reason").val('');
                $("#submits").attr("action", action);
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();
    }
    function submit_delete() {
        var contentDiv = createContentDiv($T("This action is irreversible. Are you sure you want to <strong>delete</strong> the booking?"));
        new ConfirmPopup($T("Delete booking"), contentDiv, function(confirmed) {
            if(confirmed) {
                $("#submits").attr("action", "${ url_for('rooms.roomBooking-deleteBooking', reservation ) }");
                $("#submits").submit();
            }
        }, $T("Yes"), $T("No")).open();
    }
</script>

<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">

  <!-- Status -->
  <div id="statusHelp" class="tip">
    ${ _('Validity') }:<br />
    <ul>
      <li class="tip-no-borders">
        ${ _('<b>Not confirmed</b> - the pre-booking is not confirmed (yet) by person responsible.') }
      </li>
      <li class="tip-no-borders">
        ${ _('<b>Cancelled</b> - the booking was cancelled by the requestor himself.') }
      </li>
      <li class="tip-no-borders">
        ${ _('<b>Rejected</b> - the booking was rejected by the person responsible for a room.') }
      </li>
      <li class="tip-no-borders">
        ${ _('<b>Valid</b> - the booking is confirmed and not cancelled. Note that for most rooms bookings are automatically confirmed.') }
      </li>
    </ul>
    ${ _('Time') }:<br />
    <ul>
      <li class="tip-no-borders">
        ${ _('<b>Live</b> - the booking will take place in the future.') }
      </li>
      <li class="tip-no-borders">
        ${ _('<b>Archived</b> - the booking already passed and it will never repeat in the future.') }
      </li>
    </ul>
  </div>
  <img style="border-style: solid; border-width: thick; border-color: #101010;" />
  <!-- Repetition type -->
  <div id="repetitionTypeHelp" class="tip">
    ${ _('Repetition type - this indicates how a booking repeats itself.') }
  </div>
  <!-- Where is key? -->
  <div id="whereIsKeyHelp" class="tip">
    ${ _('How to obtain a key? Often just a phone number.') }
  </div>
  <!-- Created -->
  <div id="createdHelp" class="tip">
    ${ _('When the booking was made?') }
  </div>
  <!-- Created -->
  <div id="iWillUseVideoConferencing" class="tip">
    ${ _('Is user going to use videoconferencing equipment?') }<br />
  </div>
  <div id="iNeedAVCSupport" class="tip">
    ${ _('Has user requested support for videoconferencing equipment?') }<br />
  </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<table cellpadding="0" cellspacing="0" border="0" width="100%">
  <tr>
    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">
      &nbsp;
    </td> <!-- lastvtabtitle -->
  </tr>
  <tr>
    <td class="bottomvtab" width="100%">
      <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
        <tr>
          <td class="maincell">
            <span class="formTitle" style="border-bottom-width: 0px">
              ${ _('PRE-Booking') if reservation.is_pending else _('Booking') } (${ reservation.room.name })
            </span><br /> <!-- PRE-Booking or Booking -->
            <!-- Action result message-->
            % if actionSucceeded:
              <p class="successMessage">${ title } <br/> ${ description }</p>
            % endif

            <!-- Warning for pre-bookings -->
            % if reservation.is_pending:
              <p class="warningMessage">
                ${ _('Please note that this is a <b>pre-booking</b>. This means that you shouldn\'t use the room unless you receive the confirmation that it has been accepted.') }
              </p>
            % endif
            <table width="90%" align="left" border="0">
              <!-- ROOM -->
              <tr>
                <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                  <span class="titleCellFormat">${ _('Room') }</span>
                </td>
                <td>
                  <table width="100%">
                    <tr>
                      <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Name') }&nbsp;&nbsp;
                      </td>
                      <td align="left" class="blacktext">
                        <a href="${ url_for(endpoints['room_details'], event, reservation.room) }">
                          ${ reservation.room.full_name }
                        </a>
                      </td>
                    </tr>
                    % if reservation.room.photo_id is not None:
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Interior') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="thumbnail">
                          <a href="${ reservation.room.large_photo_url }" class="js-lightbox">
                            <img border="1px" src="${ reservation.room.small_photo_url }"/>
                          </a>
                        </td>
                      </tr>
                    % endif
                    <tr>
                      <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Capacity') }&nbsp;&nbsp;
                      </td>
                      <td align="left" class="blacktext">
                        ${ reservation.room.capacity }&nbsp;${ _('seats') }
                      </td>
                    </tr>
                    <tr>
                      <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Room key') }&nbsp;&nbsp;
                      </td>
                      <td align="left" class="blacktext">
                        ${ reservation.room.key_location }${ contextHelp('whereIsKeyHelp') }
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr><td>&nbsp;</td></tr>
              <!-- WHEN -->
              <tr>
                <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                  <span class="titleCellFormat">${ _('When') }</span>
                </td>
                <td>
                  <table width="100%">
                    <tr>
                      <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Dates') }&nbsp;&nbsp;
                      </td>
                      <td align="left" class="blacktext">${ formatDate(reservation.start_dt.date()) } &mdash; ${ formatDate(reservation.end_dt.date()) }
                      </td>
                    </tr>
                    <tr>
                      <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Hours') }&nbsp;&nbsp;
                      </td>
                      <td align="left" class="blacktext">
                        ${ formatTime(reservation.start_dt) } &mdash; ${ formatTime(reservation.end_dt) }
                      </td>
                    </tr>
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Type') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ repetition }${contextHelp('repetitionTypeHelp') }
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr><td>&nbsp;</td></tr>
                <!-- BOOKED FOR -->
                <tr>
                  <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                    <span class="titleCellFormat"> ${ _('Booked for') }</span>
                  </td>
                  <td>
                    <table width="100%">
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Name') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ verbose(reservation.booked_for_name) }
                        </td>
                      </tr>
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('E-mail') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          <a style="font-weight: normal" href="mailto:${ verbose(reservation.contact_email) }">${ reservation.contact_email.replace(',',', ') }
                          </a>
                        </td>
                      </tr>
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Telephone') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ verbose(reservation.contact_phone) }
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr><td>&nbsp;</td></tr>
                <!-- CREATED -->
                <tr>
                  <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                    <span class="titleCellFormat"> ${ _('Created') }</span>
                  </td>
                  <td>
                    <table width="100%">
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('By') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ reservation.created_by_user.full_name if reservation.created_by_user else '' }
                        </td>
                      </tr>
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Date') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ formatDateTime(reservation.created_dt) } ${contextHelp('createdHelp') }
                        </td>
                      </tr>
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top">
                          ${ _('Reason') }&nbsp;&nbsp;
                        </td>
                        <td align="left" class="blacktext">
                          ${ reservation.booking_reason }
                        </td>
                      </tr>
                      % if reservation.room.has_vc:
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Video-conf.') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ _('yes') if reservation.uses_vc else _('no') }
                            % if vc_equipment:
                              <span style="color: grey;">(${ vc_equipment })</span>
                            % endif
                            ${ contextHelp('iWillUseVideoConferencing') }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top" nowrap>
                            ${ _('Video-conf Assistance') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(reservation.needs_vc_assistance, 'no') }
                            ${ contextHelp('iNeedAVCSupport') }
                          </td>
                        </tr>
                      % endif
                      % if assistance_emails and reservation.room.notification_for_assistance:
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top" nowrap>
                            ${ _('Startup Assistance') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(reservation.needs_assistance, 'no') }
                          </td>
                        </tr>
                      % endif
                      % if reservation.is_rejected:
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Rejection') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ reservation.rejection_reason }
                          </td>
                        </tr>
                      % endif
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Status') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ reservation.status_string }
                            ${contextHelp('statusHelp') }
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                  <!-- ACTIONS -->
                  <tr>
                    <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                      <span class="titleCellFormat">${ _('Actions') }</span>
                    </td>
                    <td>
                    <form id="submits" name="submits" action="" method="post">
                      <input type="hidden" name="csrf_token" value="${ _session.csrf_token }">
                      <input type="hidden" id="reason" name="reason">
                      <div style="float:left; padding-top: 15px;">
                        % if not reservation.is_cancelled and not reservation.is_rejected:
                          % if reservation.can_be_cancelled(_session.user):
                            <a class="i-button" href="#" onclick="submit_cancel(); return false;">${ _('Cancel') }</a>
                          % endif
                          % if reservation.can_be_accepted(_session.user) and not reservation.is_accepted:
                            <a class="i-button" href="#" onclick="submit_accept(); return false;">${ _('Accept') }</a>
                          % endif
                          % if reservation.can_be_rejected(_session.user):
                            <a class="i-button" href="#" onclick="submit_reject(); return false;">${ _('Reject') }</a>
                          % endif
                          % if reservation.can_be_modified(user):
                            <a class="i-button" href="${ url_for(endpoints['booking_modify'], event, reservation)}">${ _('Modify') }</a>
                          % endif
                        % endif
                        % if reservation.can_be_deleted(user):
                          <a class="i-button" href="#" onclick="submit_delete(); return false;">${ _('Delete') }</a>
                        % endif
                        <a class="i-button" href="${ url_for(endpoints['booking_clone'], event, reservation) }">${ _('Clone') }</a>
                      </div>
                    </form>
                  </td>
                </tr>
                % if edit_logs and (reservation.created_by_user == user or reservation.room.is_owned_by(user) or rb_is_admin(user)):
                  <tr><td>&nbsp;</td></tr>
                  <!-- BOOKING HISTORY -->
                  <tr>
                      <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                        <span class="titleCellFormat">${ _('Booking History') }</span>
                      </td>
                      <td>
                          <dl class="booking-history">
                              % for i, entry in enumerate(edit_logs):
                                  % if i == 1:
                                      </dl>
                                      <dl class="booking-history old" style="display: none;">
                                  % endif
                                  <dt>${ formatDateTime(entry.timestamp) }</dt>
                                  <dd>
                                      <strong>${ entry.info[0] }</strong> ${ _('by') } ${ entry.user_name }
                                      % if len(entry.info) > 1:
                                          (<a class="js-history-show-details" href="#" data-other-text="${ _('Hide Details') }">${ _('Show Details') }</a>)
                                      % endif
                                  </dd>
                                  % for detail in entry.info[1:]:
                                      <dd style="display: none;">
                                          ${ detail }
                                      </dd>
                                  % endfor
                              % endfor
                          </dl>
                          % if len(edit_logs) > 1:
                              <a href="#" class="js-history-show-old" data-other-text="${ _('Hide older history') }">${ _('Show older history') }</a>
                          % endif
                          <script>
                              $('.js-history-show-details').on('click', function(e) {
                                  e.preventDefault();
                                  var $this = $(this);
                                  var otherText = $this.data('otherText');
                                  $this.data('otherText', $this.text()).text(otherText);
                                  $(this).closest('dd').nextUntil(':not(dd)').slideToggle();
                              });

                              $('.js-history-show-old').on('click', function(e) {
                                  e.preventDefault();
                                  var $this = $(this);
                                  var otherText = $this.data('otherText');
                                  $this.data('otherText', $this.text()).text(otherText);
                                  $('.booking-history.old').slideToggle();
                              });
                          </script>
                      </td>
                  </tr>
                % endif
              % if reservation.repeat_frequency and excluded_days:
                <tr><td>&nbsp;</td></tr>
                <!-- Excluded dates -->
                <tr>
                  <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                    <span class="titleCellFormat"> ${ _('Excluded days') }</span>
                  </td>
                  <td>
                    <table width="100%">
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                          ${ _('These days are NOT booked.') }
                        </td>
                        <td align="left" class="excluded" class="blacktext">
                          % for occurrence in excluded_days:
                            % if occurrence.is_rejected:
                              ${ formatDate(occurrence.date) } (${ _('Rejected') }${ u': {}'.format(occurrence.rejection_reason) if occurrence.rejection_reason else '' })<br />
                            % elif occurrence.is_cancelled:
                              ${ formatDate(occurrence.date) } (${ _('Cancelled') }${ u': {}'.format(occurrence.rejection_reason) if occurrence.rejection_reason else '' })<br />
                            % endif
                          % endfor
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              % endif
              % if reservation.repeat_frequency:
                <tr><td>&nbsp;</td></tr>
                <!-- Occurrences -->
                <tr>
                  <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                    <span class="titleCellFormat">${ _('Occurrences') }</span>
                  </td>
                  <td>
                    <table width="100%">
                      <tr>
                        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 4px;">
                          ${ _('These days are booked.') }
                        </td>
                        <td align="left" class="blacktext">
                          % for occurrence in valid_occurrences:
                          ${ formatDate(occurrence.start_dt.date()) }
                            % if reservation.can_be_rejected(_session.user):
                              <a class="roomBookingRejectOccurrence" href="#" onclick="submit_reject_occurrence('${ url_for(endpoints['booking_occurrence_reject'], event, reservation, date=formatDate(occurrence.start_dt.date(), format='yyyy-MM-dd')) }', '${ formatDate(occurrence.start_dt.date()) }'); return false;">
                                ${ _('Reject') }
                              </a>
                            % endif
                            % if reservation.can_be_cancelled(_session.user):
                              <a class="roomBookingCancelOccurrence" href="#" onclick="submit_cancel_occurrence('${ url_for(endpoints['booking_occurrence_cancel'], event, reservation, date=formatDate(occurrence.start_dt.date(), format='yyyy-MM-dd')) }', '${ formatDate(occurrence.start_dt.date()) }'); return false;">
                                ${ _('Cancel') }
                              </a>
                            % endif
                            <br />
                          % endfor
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              % endif
              % if (not reservation.is_accepted and (rb_is_admin(user) or reservation.room.is_owned_by(user)) and reservation.find_overlapping().count()):
                <% conflicting_occurrences = reservation.get_conflicting_occurrences() %>
                % if conflicting_occurrences:
                  <tr><td>&nbsp;</td></tr>
                  <!-- Occurrences -->
                  <tr>
                    <td class="bookingDisplayTitleCell" style="vertical-align: top;">
                      <span class="titleCellFormat"> ${ _('Conflicts at the same time') }</span>
                    </td>
                    <td>
                    % for conflicts in conflicting_occurrences.itervalues():
                      % for occ in itertools.chain(conflicts['confirmed'], conflicts['pending']):
                        <strong>
                          ${ _('Booking') if occ.reservation.is_accepted else _('Pre-Booking') }:
                        </strong>
                        ${ occ.reservation.booked_for_name },
                        ${ format_datetime(occ.reservation.start_dt, 'short') } - ${ format_datetime(occ.reservation.end_dt, 'short') }
                        (<a href="${ url_for(endpoints['booking_details'], occ.reservation) }" target="_blank">${ _('show this booking') }</a>)<br>
                      % endfor
                    % endfor
                    </td>
                  </tr>
                % endif
              % endif
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<br />
