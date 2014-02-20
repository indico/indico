<script type="text/javascript">

    function adjustDates(s, e) {
        if (s.datepicker('getDate') > e.datepicker('getDate'))
            e.datepicker('setDate', s.datepicker('getDate'));
    }

    function initWidgets() {
        var s = $('#start_date'), e = $('#end_date');
        $('#start_date, #end_date').datepicker({
            showOn: 'both',
            buttonImage: imageSrc('calendarWidget'),
            buttonImageOnly: true,
            buttonText: "${ _('Choose Date') }",
            dateFormat: 'dd-mm-yy',
            onSelect: function() {
                adjustDates(s, e);
                $('searchForm').trigger('change');
            }
        });
        s.datepicker('setDate', '+0');
        e.datepicker('setDate', '+7');

        $('#timeRange').slider({
            range: true,
            max: 1439,
            values: [510, 1050],
            step: 5,
            create: function(e, ui) {
                updateTimeSlider(e, ui);
            },
            start: function(e, ui) {
                updateTimeSlider(e, ui);
            },
            slide: function(e, ui) {
                updateTimeSlider(e, ui);
            }
        });

        $('#sTime').val('0:00');
        $('#eTime').val('23:59');
        updateTimeSlider();
    }

    function confirm_search() {
        if ($('#is_only_mine').is(':checked') || $('#roomIDList').val() !== null) {
            return true;
        }
        try { if ($('#is_only_my_rooms').is(':checked')) { return true; } } catch (err) {}
        new AlertPopup($T('Select room'), $T('Please select a room (or several rooms).')).open();
        return false;
    }

    // Reads out the invalid textboxes and returns false if something is invalid.
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
        if (!is_date_valid($('#start_date').val())) {
            isValid = false;
            $('#start_date').addClass('invalid');
        }
        if (!is_date_valid($('#end_date').val())) {
            isValid = false;
            $('#end_date').addClass('invalid');
        }

        // Simple search
        var s = $('#sTime'), e = $('#eTime');

        if (s.val() == '' && onSubmit) {
            s.val('00:00');
        } else if (!is_time_valid(s.val())) {
            isValid = false;
            s.addClass('invalid');
        }

        if (e.val() == '' && onSubmit) {
            e.val('00:00');
        } else if (!is_time_valid(e.val())) {
            isValid = false;
            e.addClass('invalid');
        }

        // Holidays warning
        if (isValid && !onSubmit) {
            var lastDateInfo = searchForm.data('lastDateInfo');
            var dateInfo = $('#start_date, #sTime, #end_date, #eTime').serialize();
            console.log(dateInfo);
            if (dateInfo != lastDateInfo) {
                searchForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource(
                    'roomBooking.getDateWarning', searchForm.serializeObject()
                );

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $E('holidays-warning').set(holidaysWarning.get());
                    }
                });
            }
        }
        return isValid;
    }

    $(function() {
        initWidgets();

        $('#is_only_bookings').change(function() {
            if(this.checked) {
                $('#is_only_pre_bookings').prop('checked', false);
            }
        });

        $('#is_only_pre_bookings').change(function() {
            if(this.checked) {
                $('#is_only_bookings').prop('checked', false);
            }
        });

        $('#searchForm').delegate(':input', 'keyup change', function() {
            forms_are_valid();
        }).submit(function(e) {
            if (!forms_are_valid(true)) {
                new AlertPopup($T('Error'), $T('There are errors in the form. Please correct fields with red background.')).open();
                e.preventDefault();
            }
            else if(!confirm_search()) {
                e.preventDefault();
            }
            else {
                $('#start_date').val($('#start_date').val() + ' ' + $('#sTime').val());
                $('#end_date').val($('#end_date').val() + ' ' + $('#eTime').val());
            }
        });
    });
</script>

<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <!-- Choose Button -->
  <div id="chooseButtonHelp" class="tip">
    ${ _('Directly choose the room.') }
  </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<table cellpadding="0" cellspacing="0" border="0" width="80%">
  <tr>
    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;
    </td> <!-- lastvtabtitle -->
  </tr>
  <tr>
    <td class="bottomvtab" width="100%">
      <!-- Main cell -->
      <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
        <tr>
          <td class="maincell">
            <h2 class="page_title">
              ${ _('Search for bookings') }
            </h2>
            <!-- Background table (adds image) -->
            <table width="100%" class="ACtab">
              <tr>
                <td>
                  <form id="searchForm" method="post" action="${ roomBookingBookingListURL }">
                    <table width="90%" align="center" border="0">
                      <tr>
                        <td colspan="2">
                          <h2 class="group_title">
                            ${ _('Simple Search') }
                          </h2>
                        </td>
                      </tr>
                      <!-- For room -->
                      <tr>
                        <td nowrap="nowrap" class="titleCellTD">
                          <span class="titleCellFormat">${ _('Room') }</span>
                        </td>
                        <td width="80%">
                          <table width="100%">
                            <tr>
                              <td class="subFieldWidthSmaller" align="right">
                                <small> ${ _('Name') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left" class="blacktext" style="width: %100;">
                                <select name="room_id_list" id="roomIDList" multiple="multiple" size="8">
                                  <option value="-1">${ _('All Rooms') }</option>
                                  % for room in rooms:
                                    <option value="${ room.id }" class="${ room.kind }">
                                      ${ room.location.name }&nbsp;${ room.getFullName() }
                                    </option>
                                  % endfor
                                </select>
                                ${ inlineContextHelp(_('You can select multiple rooms the same way you select multiple files in Windows - press (and hold) left mouse button and move the cursor. Alternatively you can use keyboard - hold SHIFT and press up/down arrows.')) }
                                <input type="hidden" name="is_search" value="y" />
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr >
                        <td class="titleCellTD" style="width: 125px;">
                          <span class="titleCellFormat"> ${ _('Spans over') } </span>
                        </td>
                        <td>
                          <table width="100%">
                            <tr id="sdatesTR" >
                              <td class="subFieldWidth" align="right">
                                <small> ${ _('Start Date') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left">
                                <span id="sDatePlace">
                                  <input type="text" name="start_date" id="start_date" readonly/>
                                </span>
                              </td>
                            </tr>
                            <tr id="edatesTR" >
                              <td class="subFieldWidth" align="right" >
                                <small> ${ _('End Date') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left">
                                <span id="eDatePlace">
                                  <input type="text" name="end_date" id="end_date" readonly/>
                                </span>
                              </td>
                            </tr>
                            <tr id="hoursTR">
                              <td align="right" class="subFieldWidth">
                                <small> ${ _('Hours') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left">
                                <span id="timePlace" style="margin-left: 2px;">
                                  <input name="start_time" id="sTime" maxlength="5" size="5" type="text" readonly/> &nbsp;&mdash;&nbsp;
                                  <input name="end_time" id="eTime" maxlength="5" size="5" type="text"/ readonly>
                                  <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
                                </span>
                              </td>
                              <tr>
                                <td colspan="2" align="right">
                                  <div style="margin: 10px 0px 30px 30px; padding-top: 10px;">
                                    <div id="minHour" style="float: left; color: gray; padding-right: 12px">0:00</div>
                                    <div id="timeRange" style="width: 390px; float: left;"></div>
                                    <div id="maxHour" style="float: left; color: gray; padding-left: 12px">23:59</div>
                                    <div id="sTimeBubble" style="position: absolute; margin: -19px 0px 0px -8px;">&nbsp;</div>
                                    <div id="eTimeBubble" style="position: absolute; margin: 20px 0px 0px -8px;">&nbsp;</div>
                                  </div>
                                </td>
                              </tr>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <!-- Booked for -->
                      <tr>
                        <td class="titleCellTD" style="width: 125px;">
                          <span class="titleCellFormat"> ${ _('Booked for') }</span>
                        </td>
                        <td align="right">
                          <table width="100%">
                            <tr>
                              <td class="subFieldWidthSmaller" align="right">
                                <small> ${ _('Name') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left" class="blacktext">
                                <input size="30" type="text" id="booked_for_name" name="booked_for_name" />
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <!-- Reason -->
                      <tr>
                      <td class="titleCellTD" style="width: 125px;">
                        <span class="titleCellFormat"> ${ _('Reason') }</span>
                      </td>
                      <td align="right">
                        <table width="100%">
                          <tr>
                            <td class="subFieldWidthSmaller" align="right">
                              <small> ${ _('Reason') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext">
                              <input size="30" type="text" id="reason" name="reason" />
                            </td>
                          </tr>
                        </table>
                        <input id="submitBtn1" type="submit" class="btn" value="${ _('Search') }" />
                      </td>
                    </tr>
                  </table>
                  <br>
                  <table width="90%" align="center" border="0">
                    <tr>
                      <td colspan="2">
                        <h2 class="group_title">
                          ${ _('Advanced search') }
                        </h2>
                      </td>
                    </tr>
                    <tr>
                      <td nowrap class="titleCellTD" style="width: 125px;">
                        <span class="titleCellFormat"> ${ _("Attributes")}
                      </td>
                      <td align="right">
                        <table width="100%" cellspacing="4px">
                          <tr>
                            <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap">
                              <small>${ _('Only Bookings') } &nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="is_only_bookings" name="is_only_bookings" type="checkbox" />
                              ${ inlineContextHelp( _('Show only <b>Bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.')) }
                              <br />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Only Pre-bookings') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext">
                              <input id="is_only_pre_bookings" name="is_only_pre_bookings" type="checkbox" />
                            ${ inlineContextHelp( _('Show only <b>PRE-bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.')  ) }
                              <br />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Only mine') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="is_only_mine" name="is_only_mine" type="checkbox" />
                                ${ inlineContextHelp(_('Show only <b>your</b> bookings.')) }
                              <br />
                            </td>
                          </tr>
                          % if isResponsibleForRooms:
                            <tr>
                            <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                                <small>${ _('Of my rooms') }&nbsp;&nbsp;</small>
                              </td>
                              <td align="left" class="blacktext">
                                <input id="is_only_my_rooms" name="is_only_my_rooms" type="checkbox" />
                              ${ inlineContextHelp(_('Only bookings of rooms you are responsible for.')) }
                                <br />
                              </td>
                            </tr>
                          % endif
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Is rejected') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="is_rejected" name="is_rejected" type="checkbox" />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Is cancelled') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext">
                              <input id="is_cancelled" name="is_cancelled" type="checkbox" />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Is archival') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="is_archival" name="is_archival" type="checkbox" />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Uses video-conf.') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="uses_video_conference" name="uses_video_conference" type="checkbox" />
                            ${ inlineContextHelp(_('Show only bookings which will use video   conferencing systems.')) }
                              <br />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                            <small>${ _('Assistance for video-conf. startup') }&nbsp;&nbsp;</small  >
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="needs_video_conference_setup" name="needs_video_conference_setup" type="checkbox" />
                            ${ inlineContextHelp(_('Show only bookings which requested assistance   for the startup of the videoconference session.')) }
                              <br />
                            </td>
                          </tr>
                          <tr>
                          <td style="width:165px; text-align: right; vertical-align: top; white-  space: nowrap">
                              <small>${ _('Assistance for meeting startup') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="needs_general_assistance" name="needs_general_assistance" type="checkbox" />
                            ${ inlineContextHelp(_('Show only bookings which requested assistance   for the startup of the meeting.')) }
                              <br />
                            </td>
                          </tr>
                          <tr>
                            <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap">
                            <small>${ _('Is heavy') }&nbsp;&nbsp;</small>
                            </td>
                            <td align="left" class="blacktext" >
                              <input id="is_heavy" name="is_heavy" type="checkbox" />
                              ${ inlineContextHelp(_('Show only <b>heavy</b> bookings.')) }
                              <br />
                            </td>
                          </tr>
                        </table>
                        <input id="submitBtn2" type="submit" class="btn" value="${ _('Search') }" />
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
