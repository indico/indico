<script>
    // Reads out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid(onSubmit) {
        if (onSubmit != true) {
            onSubmit = false;
        }

        // Init, clean up (make all textboxes white again)
        var bookingForm = $('#bookingForm');
        $(':input', bookingForm).removeClass('invalid');


        // Holidays warning
        if (!onSubmit) {
            var lastDateInfo = bookingForm.data('lastDateInfo');
            var dateInfo = $('#sDay, #sMonth, #sYear, #eDay, #eMonth, #eYear').serialize();
            if (dateInfo != lastDateInfo) {
                bookingForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource('roomBooking.getDateWarning', bookingForm.serializeObject());

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $('#holidays-warning').html(holidaysWarning.get());
                        if (holidaysWarning.get() == '')
                            $('#holidays-warning').hide();
                        else
                            $('#holidays-warning').show();
                    }
                });
            }
        }

        var isValid = true;
        % if not infoBookingMode:
            // Date validator (repeatability)
            isValid = validate_period(true, ${ allow_past | n, j }, 1, $('#repeatability').val()) && isValid; // 1: validate dates
            // Time validator
            isValid = isValid & $('#timerange').timerange('validate');
        % endif
        required_fields(['reservation-booked_for_name', 'reservation-contact_email', 'reservation-booking_reason']) && isValid;
        if (onSubmit) {
            isValid = required_fields(['reservation-booked_for_name', 'reservation-contact_email', 'reservation-booking_reason']) && isValid;
        } else {
            isValid = required_fields(['reservation-booked_for_name', 'reservation-contact_email']) && isValid;
        }
        % if not infoBookingMode and not (user.isRBAdmin() or user.getId() == room.owner_id) and room.max_advance_days > 0:
            isValid = validate_allow(${ room.max_advance_days }) && isValid;
        % endif
        if (!Util.Validation.isEmailList($('#reservation-contact_email').val())) {
            isValid = false;
            $('#reservation-contact_email').addClass('invalid');
        }

        % if room.needs_video_conference_setup:
            var vcIsValid = true;
            if ($('#reservation-uses_video_conference').is(':checked')) {
                vcIsValid = $('input.videoConferenceOption').is(':checked');
            }
            $('#vcSystemList').toggleClass('invalid', !vcIsValid);
            isValid = isValid && vcIsValid;
        % endif

        return isValid;
    }

    function searchForUsers() {
            var popup = new ChooseUsersPopup($T('Select a user'),
                                         true,
                                         null, false,
                                         true, null,
                                         true, true, false,
                                         function(users) {
                                             $E('reservation-booked_for_name').set(users[0].name);
                                             $E('reservation-booked_for_id').set(users[0].id);
                                             $E('reservation-contact_email').set(users[0].email);
                                             $E('reservation-contact_phone').set(users[0].phone);
                                         });

            popup.execute();
    }

    function isBookable() {
        // Get the room location and id in the SELECT
        var roomLocation = $("#roomName option:selected").data("location");
        var roomID = $("#roomName option:selected").data("id");

        // Send an asynchronous request to the server
        // Depending of result, either recheck the conflicts
        // Relaod Room Booking form or pop up a dialog
        indicoRequest('user.canBook',
            {roomLocation: roomLocation, roomID: roomID},
            function(result, error) {
                if(!error) {
                    if (result) {
                        $("#roomLocation").val(roomLocation);
                        $("#roomID").val(roomID);
                        $("#bookingForm").submit();
                    } else {
                        //bookButtonWrapper.set(bookButton);
                        var popup = new AlertPopup($T('Booking Not Allowed'),
                                $T("You're not allowed to book this room"));
                        popup.open();
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            });
    }

    function saveBooking() {
        $('#bookingForm').attr('action', '${ saveBookingUH }');
        if (forms_are_valid(true))
            $('#bookingForm').submit();
        else
            new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
    }

    function checkBooking() {
        $('#bookingForm').attr('action', '${ bookingFormURL }#conflicts');
        $('#bookingForm').submit();
    };

    $(window).on('load', function() {

        % if showErrors:
            var popup = new ExclusivePopupWithButtons($T('Booking failed'), function(){popup.close();}, false, false, true);

            popup._getButtons = function() {
                var self = this;
                return [
                    [$T('Change Search Criteria'), function() {
                        window.location='${ urlHandlers.UHRoomBookingBookRoom.getURL() }';
                        self.close();
                    }],
                    [$T('Close'), function() {
                        self.close();
                    }],
                ];
            }
            popup.draw = function(){
                var errorList = "";
                % for error in errors:
                    errorList +="${error}. ";
                % endfor
                var span1 = Html.span('', $T(errorList));
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, Widget.block([span1, Html.br()]), {maxWidth: pixels(500)});
            };
            popup.open();

        % elif room.needs_video_conference_setup:
            $('.videoConferenceOption, #needsAVCSupport').change(function() {
                if(this.checked) {
                    $('#reservation-uses_video_conference').prop('checked', true);
                }
            });
            $('#reservation-uses_video_conference').change(function() {
                if(!this.checked) {
                    $('.videoConferenceOption, #reservation-needs_video_conference_setup').prop('checked', false);
                }
            });
        % endif

        $('#bookingForm').submit(function(e) {
            if (!forms_are_valid()) {
                e.preventDefault();
                 new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
            };
        }).keydown(function(e) {
            if(e.which == 13 && !$(e.target).is('textarea, :submit')) {
                e.preventDefault();
                saveBooking();
            }
        });

        if (forms_are_valid()) {
            set_repeatition_comment();
        }
    });
</script>

<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <!-- Where is key? -->
  <div id="whereIsKeyHelp" class="tip">
    ${ _('How to obtain a key? Often just a phone number.') }
  </div>
  <div id="skipConflictsHelp" class="tip">
    ${ _('Creates or saves your booking only for available dates. All conflicting days will be excluded.') }
  </div>
  <div id="iWillUseVideoConferencing" class="tip">
    ${ _('Check <b>if</b> you are going to use video-conferencing equipment.') }
    <br />
  </div>
  <div id="iNeedAVCSupport" class="tip">
    ${ _('Check <b>if</b> you need AVC Support to help you with video-conferencing equipment.') }<br />
  </div>
  <%include file="CHBookingRepetition.tpl"/>
</div>
<!-- END OF CONTEXT HELP DIVS -->
<form id="bookingForm" name="bookingForm" action="${ bookingFormURL }" method="post">
  <input type="hidden" id="afterCalPreview" name="afterCalPreview" value="True" />

  <table style="width: 100%; padding-left: 20px;">
    % if standalone:
      <tr>
        <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
      </tr>
    % endif
    <tr>
      <td>
        <input type="hidden" name="roomID" id="roomID" value="${ room.id }"/>
        <input type="hidden" name="roomLocation" id="roomLocation" value="${ room.location.name }"/>
        <input type="hidden" name="finishDate" id="finishDate"/>
        <input type="hidden" name="sDay" id="sDay" value="${ startDT.day }"/>
        <input type="hidden" name="sMonth" id="sMonth" value="${ startDT.month }"/>
        <input type="hidden" name="sYear" id="sYear" value="${ startDT.year }"/>
        <input type="hidden" name="eDay" id="eDay" value="${ endDT.day }"/>
        <input type="hidden" name="eMonth" id="eMonth" value="${ endDT.month }"/>
        <input type="hidden" name="eYear" id="eYear" value="${ endDT.year }"/>
        % if infoBookingMode:
          <input type="hidden" value="${ startT }" name="sTime" id="sTime"/>
          <input type="hidden" value="${ endT }" name="eTime" id="eTime"/>
          <ul id="breadcrumbs" style="margin:0px 0px 0px -15px; padding: 0; list-style: none;">
            <li>
              <span>
                <a href="${ urlHandlers.UHRoomBookingBookRoom.getURL() }">
                  ${_("Specify Search Criteria") }
                </a>
              </span>
            </li>
            <li>
              <span>
                <!-- TODO: adapt rh -->
                <a href="#" onclick="history.back(); return false;">
                  ${ _('Select Available Period') }
                </a>
              </span>
            </li>
            <li>
              <span class="current">
                ${ _('Confirm Reservation') }
              </span>
            </li>
          </ul>
        % elif isModif:
          <span class="page-title">
            ${ _('Modify') }&nbsp;${ bookingMessage }ing
            <input type="hidden" name="resvID" id="resvID" value="${ form.id }" />
          </span>
        % else:
          <h2 class="page-title">
            ${ _('New') }&nbsp;${ bookingMessage }ing
          </h2>
        % endif
        <table width="100%" align="left" border="0">
          <%include file="RoomBookingRoomMiniDetails.tpl" args="room=room"/>
          <tr>
            <td>
              <div class="groupTitle bookingTitle">${'Booking Time & Date'}</div>
            </td>
          </tr>
          <!-- BOOKING TIME & DATE -->
          <tr>
            <td>
              <table id="roomBookingTable">
                <%include file="RoomBookingPeriodForm.tpl"
                    args="repeatability=(form.repeat_unit.data, form.repeat_step.data),
                          form=0,
                          unavailableDates=room.getNonBookableDates(skip_past=True),
                          availableDayPeriods=room.getBookableTimes(),
                          maxAdvanceDays=room.max_advance_days"/>
              </table>
            </td>
          </tr>
          % if not infoBookingMode:
            <tr>
              <td id="conflicts" colspan="2">
                ${ room_calendar }
              </td>
            </tr>
          % endif
          <!-- BOOKED FOR -->
          <tr>
            <td>
              <div class="groupTitle bookingTitle">${ _('Being Booked For') }</div>
            </td>
          </tr>
          <tr>
            <td>
              <table width="100%">
                % if rh._requireRealUsers:
                  <tr>
                    <td class="subFieldWidth" align="right" valign="top">
                      ${ _('User') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                      ${ form.booked_for_id }
                      ${ form.booked_for_name(style='width: 240px;', onclick='searchForUsers();', readonly=True) }
                      <input type="button" value="Search" onclick="searchForUsers();" />
                      ${ inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) }
                    </td>
                  </tr>
                % else:
                  <tr>
                    <td class="subFieldWidth" align="right" valign="top">
                      ${ _('Name') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                      ${ form.booked_for_name(style='width: 240px;') }
                      ${ inlineContextHelp(_("<b>Required.</b> For whom the booking is made.")) }
                    </td>
                  </tr>
                % endif
                <tr>
                  <td class="subFieldWidth" align="right" valign="top">
                    ${ _('E-mail') }&nbsp;&nbsp;
                  </td>
                  <td align="left" class="blacktext">
                    ${ form.contact_email(style='width: 240px;') }
                    ${ inlineContextHelp(_('<b>Required.</b> Contact email. You can specify more than one email address by separating them with commas, semicolons or whitespaces.')) }
                  </td>
                </tr>
                <tr>
                  <td align="right" class="subFieldWidth" valign="top">
                    ${ _('Telephone') }&nbsp;&nbsp;
                  </td>
                  <td align="left" class="blacktext">
                    ${ form.contact_phone(style='width: 240px;') }
                    ${ inlineContextHelp(_('Contact telephone.')) }
                  </td>
                </tr>
                <tr>
                  <td align="right" class="subFieldWidth" valign="top">
                    ${ _('Reason') }&nbsp;&nbsp;
                  </td>
                  <td align="left" class="blacktext">
                    ${ form.booking_reason(rows='3', cols='50') }
                    ${ inlineContextHelp(_('<b>Required.</b> The justification for booking. Why do you need this room?')) }
                  </td>
                </tr>
                % if room.needs_video_conference_setup:
                  <tr>
                    <td align="right" class="subFieldWidth" valign="top">
                      <span style="color: Red;">
                        ${ _('I will use video-conf. equipment (please only check that which you need)') }
                      </span>&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                        ${ form.uses_video_conference }
                        ${ contextHelp('iWillUseVideoConferencing') }
                    </td>
                  </tr>
                  <tr>
                    <td align="right" class="subFieldWidth" valign="middle">
                      <span style="color: Red;">
                        ${ _('I will use video-conf. system') }
                      </span>&nbsp;&nbsp;
                    </td>
                    <td align="left" id="vcSystemList" class="blacktext">
                      % for vc in room.available_video_conference:
                        <% checked = "" %>
                        % if vc in form.uses_video_conference:
                          <% checked = "checked " %>
                        % endif
                        <% htmlCheckbox = """<br>\n<input id="vc_%s" name="vc_%s" class="videoConferenceOption" type="checkbox" %s /> %s""" %>
                        ${ htmlCheckbox % (vc[:3], vc[:3], checked, vc) }
                      % endfor
                    </td>
                  </tr>
                % endif
                % if room.needs_video_conference_setup or (rh._isAssistenceEmailSetup and room.notification_for_assistance):
                  <tr>
                    <td align="right" class="subFieldWidth" valign="top">
                      ${ _('Assistance') }&nbsp;&nbsp;
                    </td>
                    <td>
                      <table valign='top' cellpadding=0 cellspacing=0>
                        % if room.needs_video_conference_setup:
                          <tr>
                            <td align="left" class="blacktext">
                              <table cellpadding=0 cellspacing=0>
                                <tr>
                                    <td style="vertical-align:top;">
                                        ${ form.needs_video_conference_setup }
                                    </td>
                                    <td style="width:100%;padding-left: 3px;">
                                      ${ _('Request assistance for the startup of the videoconference session. This support is usually performed remotely.') }
                                    </td>
                                </tr>
                              </table>
                            </td>
                          </tr>
                        % endif
                        % if rh._isAssistenceEmailSetup and room.notification_for_assistance:
                          <tr>
                            <td align="left" class="blacktext">
                              <table cellpadding=0 cellspacing=0>
                                <tr>
                                    <td style="vertical-align:top;">
                                        ${ form.needs_general_assistance }
                                    </td>
                                    <td style="width:100%;padding-left: 3px;">
                                        ${ _('Request assistance for the startup of your meeting. A technician will be physically present 10 to 15 minutes before the event to help you start up the room equipment (microphone, projector, etc)') }
                                    </td>
                                </tr>
                              </table>
                            </td>
                          </tr>
                        % endif
                      </table>
                    </td>
                  </tr>
                % endif
              </table>
            </td>
          </tr>
          <!-- ACTIONS -->
          <tr>
            <td>
              <div class="groupTitle bookingTitle"></div>
            </td>
          </tr>
          <tr>
            <td>
              <input type="hidden" name="conf" value="${ conf.getId()  if conf else ''}" />
              <input type="hidden" name="standalone" value="${ standalone }" />
              <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                <li class="button" style="margin-left: 10px" onclick="saveBooking()">
                  <a href="#" onClick="return false;">${_('Save') if isModif else bookingMessage}</a>
                </li>
                <li style="display: none"></li>
              </ul>
              <div style="padding-top: 5px;">
                <input type="checkbox" name="skipConflicting" id="skipConflicting" ${ ' checked="checked" ' if skipConflicting else "" } />
                ${ _('Skip conflicting dates') }
                ${contextHelp('skipConflictsHelp') }
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</form>
