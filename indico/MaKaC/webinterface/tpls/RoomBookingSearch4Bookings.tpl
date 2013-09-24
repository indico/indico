<script type="text/javascript">

    // Displays div with dates and hours
    function all_date_fields_are_blank() {
        return ($('#sDay').val()=='' && $('#sMonth').val()=='' && $('#sYear').val()=='' && $('#sdate').val()=='' &&
                 $('#eDay').val()=='' && $('#eMonth').val()=='' && $('#eYear').val()=='' && $('#edate').val()=='');
    }
    function all_time_fields_are_blank() {
        return $('#sTime').val() == '' && $('#eTime').val() == '';
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

        // Simple search
        if (!all_date_fields_are_blank()) {
            isValid = validate_period(false, true, 1) // 1: validate only dates
        }
        if (!all_time_fields_are_blank()) {
            isValid = isValid && validate_period(false, true, 2) // 2: validate only times
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

        return isValid;
    }

    function confirm_search() {
        if ($('#onlyMy').is(':checked')) {
            return true;
        }
        if ($('#roomGUID').val() !== null) {
            return true;
        }
        try { if ($('#ofMyRooms').is(':checked')) { return true; } } catch (err) {}
        new AlertPopup($T("Select room"), $T("Please select a room (or several rooms).")).open();
        return false;
    }

    $(function() {
        var startDate = IndicoUI.Widgets.Generic.dateField_sdate(false, null, ['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField_edate(false, null, ['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);


        /* In case the date changes, we need to check whether the start date is greater than the end date,
        and if it's so we need to change it */
        startDate.observe(function(value) {
            if (IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get())) {
                endDate.set(startDate.get());
                $(endDate.dom).trigger('change');
            }
        });

        endDate.observe(function(value) {
            if (IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get())) {
                startDate.set(endDate.get());
                $(startDate.dom).trigger('change');
            }
        });

        % if today.day != '':
            startDate.set('${ today.day }/${ today.month }/${ today.year }');
        % endif

        % if weekLater.day != '':
            endDate.set('${ weekLater.day }/${ weekLater.month }/${ weekLater.year }');
        % endif

        $('#onlyBookings').change(function() {
            if(this.checked) {
                $('#onlyPrebookings').prop('checked', false);
            }
        });

        $('#onlyPrebookings').change(function() {
            if(this.checked) {
                $('#onlyBookings').prop('checked', false);
            }
        });

        $('#searchForm').delegate(':input', 'keyup change', function() {
            forms_are_valid();
        }).submit(function(e) {
            if (!forms_are_valid(true)) {
                new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
                e.preventDefault();
            }
            else if(!confirm_search()) {
                e.preventDefault();
            }
        });
    });
</script>
        <!-- CONTEXT HELP DIVS -->
        <div id="tooltipPool" style="display: none">
            <!-- Choose Button -->
            <div id="chooseButtonHelp" class="tip">
                Directly choose the room.
            </div>
        </div>
        <!-- END OF CONTEXT HELP DIVS -->

        <table cellpadding="0" cellspacing="0" border="0" width="80%">
        <tr>
        <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
        </tr>
        <tr>
        <td class="bottomvtab" width="100%">
            <!-- Main cell -->
            <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                <tr>
                    <td class="maincell">
                        <h2 class="page_title">
                            ${_("Search for bookings")}
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
                                                    ${ _("Simple Search")}
                                                </h2>
                                            </td>
                                        </tr>
                                        <!-- For room -->
                                        <tr>
                                            <td nowrap="nowrap" class="titleCellTD"><span class="titleCellFormat"> ${ _("Room")}</span></td>
                                            <td width="80%">
                                                <table width="100%">
                                                <tr>
                                                    <td class="subFieldWidthSmaller" align="right" ><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                                                    <td align="left" class="blacktext">
                                                        <select name="roomGUID" id="roomGUID" multiple="multiple" size="8">
                                                            <option value="allRooms"> All Rooms</option>
                                                            % for room in rooms:
                                                                <option value="${ str( room.guid ) }" class="${ roomClass( room ) }">${ room.locationName + " &nbsp; " + room.getFullName() }</option>
                                                            % endfor
                                                        </select>
                                                        ${inlineContextHelp(_("You can select multiple rooms the same way you select multiple files in Windows - press (and hold) left mouse button and move the cursor. Alternatively you can use keyboard - hold SHIFT and press up/down arrows.") )}
                                                        <input type="hidden" name="search" value="on" />
                                                    </td>
                                                </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr >
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Spans over")}</span></td>
                                            <td>
                                                <table width="100%">

                                                <tr id="sdatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> ${ _("Start Date")}&nbsp;&nbsp;</small></td>
                                            <td class="blacktext">
                                                <span id="sDatePlace"></span>
                                                <input type="hidden" value="${ today.day }" name="sDay" id="sDay" />
                                                <input type="hidden" value="${ today.month }" name="sMonth" id="sMonth" />
                                                <input type="hidden" value="${ today.year }" name="sYear" id="sYear" />
                                            </td>
                                          </tr>
                                         <tr id="edatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> ${ _("End Date")}&nbsp;&nbsp;</small></td>
                                            <td>
                                                <span id="eDatePlace"></span>
                                                <input type="hidden" value="${ weekLater.day }" name="eDay" id="eDay"/>
                                                <input type="hidden" value="${ weekLater.month }" name="eMonth" id="eMonth"/>
                                                <input type="hidden" value="${ weekLater.year }" name="eYear" id="eYear"/>
                                            </td>
                                        </tr>


                                                <tr id="hoursTR" >
                                                    <td align="right" ><small> ${ _("Hours")}&nbsp;&nbsp;</small></td>
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
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Booked for")}</span></td>
                                            <td align="right">
                                                <table width="100%">
                                                    <tr>
                                                        <td class="subFieldWidthSmaller" align="right"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="30" type="text" id="bookedForName" name="bookedForName" />
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- Reason -->
                                        <tr>
                                            <td class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Reason")}</span></td>
                                            <td align="right">
                                                <table width="100%">
                                                    <tr>
                                                        <td class="subFieldWidthSmaller" align="right"><small> ${ _("Reason")}&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input size="30" type="text" id="reason" name="reason" />
                                                        </td>
                                                    </tr>
                                                </table>
                                                <input id="submitBtn1" type="submit" class="btn" value="${ _('Search')}" />
                                            </td>
                                        </tr>
                                    </table>
                                    <br>
                                    <table width="90%" align="center" border="0">
                                        <tr>
                                            <td colspan="2">
                                                <h2 class="group_title">
                                                    ${ _("Advanced search")}
                                                </h2>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td nowrap class="titleCellTD" style="width: 125px;"><span class="titleCellFormat"> ${ _("Attributes")}</td>
                                            <td align="right">
                                                <table width="100%" cellspacing="4px">
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>Only Bookings&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyBookings" name="onlyBookings" type="checkbox" />
                                                            ${inlineContextHelp(_("Show only <b>Bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>Only Pre-bookings&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyPrebookings" name="onlyPrebookings" type="checkbox" />
                                                            ${inlineContextHelp(_("Show only <b>PRE-bookings</b>. If not checked, both pre-bookings and confirmed bookings will be shown.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>Only mine&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="onlyMy" name="onlyMy" type="checkbox" />
                                                            ${inlineContextHelp(_('Show only <b>your</b> bookings.'))}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    % if isResponsibleForRooms:
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>Of my rooms&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext">
                                                            <input id="ofMyRooms" name="ofMyRooms" type="checkbox" />
                                                            ${inlineContextHelp(_("Only bookings of rooms you are responsible for.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    % endif
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Is rejected") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isRejected" name="isRejected" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Is cancelled") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isCancelled" name="isCancelled" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Is archival") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isArchival" name="isArchival" type="checkbox" />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Uses video-conf.") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="usesAVC" name="usesAVC" type="checkbox" />
                                                            ${inlineContextHelp(_('Show only bookings which will use video conferencing systems.'))}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Assistance for video-conf. startup") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="needsAVCSupport" name="needsAVCSupport" type="checkbox" />
                                                            ${inlineContextHelp(_('Show only bookings which requested assistance for the startup of the videoconference session.'))}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Assistance for meeting startup") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="needsAssistance" name="needsAssistance" type="checkbox" />
                                                            ${inlineContextHelp(_('Show only bookings which requested assistance for the startup of the meeting.'))}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="width:165px; text-align: right; vertical-align: top; white-space: nowrap"><small>${ _("Is heavy") }&nbsp;&nbsp;</small></td>
                                                        <td align="left" class="blacktext" >
                                                            <input id="isHeavy" name="isHeavy" type="checkbox" />
                                                            ${inlineContextHelp(_("[v] Show only <b>heavy</b> bookings.") )}
                                                            <br />
                                                        </td>
                                                    </tr>
                                                </table>
                                                <input id="submitBtn2" type="submit" class="btn" value="${ _('Search')}" />
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
