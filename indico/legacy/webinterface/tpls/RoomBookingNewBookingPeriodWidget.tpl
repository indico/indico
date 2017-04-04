<%page args="form=None, flexibility=False, can_override=False, min_date=None, date_changed=None, past_date=None"/>
<% from datetime import datetime %>

<!-- Slider -->
<div id="timerange"></div>

<!-- Repeatibility options -->
<div class="toolbar thin space-before space-after">
    <div id="repeatability" class="group i-selection">
        <span class="i-button label">${ _('Frequency') }</span>
        % for option in form.repeat_frequency:
            ${ option }
            ${ option.label(class_='i-button') }
        % endfor
    </div>

    % if flexibility:
        <div id="flexibleDates" class="group i-selection">
            <span class="i-button label">${ _('Flexibility') }</span>
            % for option in form.flexible_dates_range:
                ${ option }
                ${ option.label(class_='i-button') }
            % endfor
        </div>
    % endif
</div>

<!-- Datepicker -->
<div id="datePeriod">
    <div id="sDatePlaceDiv" class="datepicker" style="clear: both;">
        <div id="sDatePlaceTitle" class="datepicker-title">${ _('Booking date') }</div>
        <div id="sDatePlace"></div>
    </div>
    <div id="eDatePlaceDiv" class="datepicker" style="display:none;">
        <div id='eDatePlaceTitle' class='datepicker-title'>${ _('End date') }</div>
        <div id="eDatePlace"></div>
    </div>
    <div class="datepicker-info">
        % if room and room.max_advance_days:
            <div class="info-message-box">
                <div class="message-text">
                    ${ _('This room can only be booked {0} days in advance').format(room.max_advance_days) }
                </div>
            </div>
        % endif
        <div id="holidays-warning" class="info-message-box" style="display: none">
            <div class="message-text"></div>
        </div>
        % if past_date:
            <div class="highlight-message-box js-default-date-warning">
                <div class="message-text">
                    ${_("Looks like you were trying to book a room in the past so we moved you forward to the present.") }
                </div>
            </div>
        % endif
        % if date_changed:
            <div class="highlight-message-box js-default-date-warning">
                <div class="message-text">
                    ${ _("It's late, so we selected the next day for you.") }<br>
                    <small> ${ _("You can still select today in the calendar.") }</small>
                </div>
            </div>
        % endif
        <div class="error-message-box booking-limit-warning hidden">
            <div class="message-text">
                ${_('It is not possible to book the selected room for more than {0} days').format(booking_limit) }
            </div>
        </div>
        <div class="error-message-box booking-limit-room-warning hidden">
            <div class="message-text"></div>
        </div>
    </div>
</div>

${ form.start_dt(type='hidden') }
${ form.end_dt(type='hidden') }
${ form.repeat_interval(type='hidden') }

<script>
    $(document).ready(function() {
        'use strict';

        function checkFrequency() {
            var frequency = $('#repeatability input:radio[name=repeat_frequency]:checked').val();

            if (frequency === '0') {
                $('#sDatePlaceTitle').text("${ _('Booking date') }");
                $('#eDatePlaceDiv').hide();
                $('#repeat_interval').val('0');
            } else {
                $('#sDatePlaceTitle').text("${_('Start date')}");
                $('#eDatePlaceDiv').show();
                $('#repeat_interval').val('1');
                disableInvalidDays();
                refreshDatePicker($('#eDatePlace'));
                selectEndDate();
            }

            $('#flexibleDates input:radio').prop('disabled', frequency === '1');
        }

        function combineDatetime() {
            var startDate = moment($('#sDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var endDate = moment($('#eDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var startTime = $('#timerange').timerange('getStartTime');
            var endTime = $('#timerange').timerange('getEndTime');


            $('#start_dt').val('{0} {1}'.format(startDate, startTime));
            $('#end_dt').val('{0} {1}'.format(endDate, endTime));
        }

        function checkHolidays() {
            var data = {};
            var repeat_frequency = $('input[name=repeat_frequency]:checked').val();

            data.start_date = moment($('#start_dt').val(), 'D/MM/YYYY H:m').format('YYYY-MM-D');
            if (repeat_frequency !== '0') {
                data.end_date = moment($('#end_dt').val(), 'D/MM/YYYY H:m').format('YYYY-MM-D')
            } else {
                data.end_date = data.start_date;
            }

            var holidaysWarning = indicoSource('roomBooking.getDateWarning', data);
            holidaysWarning.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    var msg = holidaysWarning.get();
                    $('#holidays-warning .message-text').html(msg);
                    $('#holidays-warning').toggle(!!msg);
                }
            });
        }

        function disableInvalidDays() {
            var startDate = $('#sDatePlace').datepicker('getDate');
            var endMonth = +$('#eDatePlace .ui-datepicker-month').val();
            var endYear = +$('#eDatePlace .ui-datepicker-year').val();
            // Create a date on the first of the month, two months after the endMonth, endYear values.
            var endDate = new Date(endMonth > 9 ? endYear + 1 : endYear, (endMonth + 2) % 12, 1);
            var frequency = $('#repeatability input:radio[name=repeat_frequency]:checked').val();

            validEndDates = generateValidEndDates(startDate, endDate, frequencies[frequency]);
        }

        function selectEndDate() {
            var repetition = {};
            repetition[RRule.DAILY] = 'days';
            repetition[RRule.WEEKLY] = 'weeks';
            repetition[RRule.MONTHLY] = 'months';

            var startDate = $('#sDatePlace').datepicker('getDate');
            var selectedEndDate = $('#eDatePlace').datepicker('getDate');
            var frequency = frequencies[$('#repeatability input:radio[name=repeat_frequency]:checked').val()];
            var forceSetEndDate = false;
            var endDate;

            if (selectedEndDate.getTime() <= startDate.getTime()) {
                endDate = moment(startDate).add(2, repetition[frequency]).toDate();
                forceSetEndDate = true;
            } else {
                endDate = moment(selectedEndDate).add(1, repetition[frequency]).toDate();
            }
            var endDates = generateValidEndDates(startDate, endDate, frequency);

            if (endDates !== null && endDates.length &&
                    (forceSetEndDate || endDates.indexOf(selectedEndDate.getTime()) === -1)) {
                $('#eDatePlace').datepicker('setDate', getClosestDate(endDates, selectedEndDate));
                refreshDatePicker($('#eDatePlace'));
            }
        }

        function commonOnSelect() {
            $('.js-default-date-warning').fadeOut();
            combineDatetime();
            checkHolidays();
            validateForm();
        }

        function getClosestDate(dates, date) {
            // dates must be a sorted array of int which represent value in ms
            // date is a date or a date in ms
            if (date instanceof Date) {
                date = date.getTime();
            }

            var min = 0, max = dates.length - 1;
            var lo = 0, hi = dates.length - 1, mid = null;
            while (lo <= hi) {
                mid = Math.floor((lo + hi) / 2);
                if (date < dates[mid]) {
                    hi = mid - 1;
                } else if (date > dates[mid]) {
                    lo = mid + 1;
                } else {
                    return new Date(dates[mid]);
                }
            }

            // Check for invalid indexes
            if (hi < 0 && lo <= dates.length - 1) {
                return new Date(dates[lo]);
            } else if (lo > dates.length - 1 && hi >= 0) {
                return new Date(dates[hi]);
            }

            var dLo = Math.abs(date - dates[lo]);
            var dHi = Math.abs(date - dates[hi]);
            return dLo <= dHi ? new Date(dates[lo]) : new Date(dates[hi]);
        }

        function refreshDatePicker($dpElem) {
            var disabled = $dpElem.datepicker('isDisabled');
            $dpElem.datepicker('refresh');
            if (disabled) {
                $dpElem.datepicker('disable');
            }
        }

        function checkBookingLimit() {
            var oneDay = 86400 * 1000;
            var startDate = $('#sDatePlace').datepicker('getDate');
            var endDate = $('#eDatePlace').datepicker('getDate');
            var selectedDaysPeriod = (endDate - startDate) / oneDay;
            var selectedRooms;
            % if serializable_room:
                // Individual booking
                selectedRooms = [${ serializable_room | j, n }];
            % else:
                // Multiple select booking
                var selectedRoomsIndexes = $("#roomselector").roomselector("selection");
                selectedRooms = _.map(selectedRoomsIndexes, function(i) { return rooms[i]; });
            % endif
            var selectedNotLimitedRooms = _.clone(selectedRooms);
            var limitedRoomsInvalid = [];
            _.each(selectedRooms, function(room) {
                var roomBookingLimit = room.booking_limit_days;
                if (roomBookingLimit) {
                    selectedNotLimitedRooms.splice(selectedNotLimitedRooms.indexOf(room), 1);
                    if (selectedDaysPeriod > roomBookingLimit) {
                        limitedRoomsInvalid.push(room);
                    }
                }
            });
            handleLimitedRoomsInvalid(limitedRoomsInvalid);
            if (selectedNotLimitedRooms.length) {
                var bookingDaysLimit = ${ booking_limit };
                var isLimitExceeded = endDate > startDate && selectedDaysPeriod > bookingDaysLimit;
                $('.booking-limit-warning').toggleClass('hidden', !isLimitExceeded);
                $('#searchForm :submit, #bookingForm :submit').prop('disabled', isLimitExceeded);
            } else {
                $('.booking-limit-warning').addClass('hidden');
                $('#searchForm :submit, #bookingForm :submit').prop('disabled', !!limitedRoomsInvalid.length);
            }
        }

        function handleLimitedRoomsInvalid(rooms) {
            if (rooms.length) {
                var warningMsgRooms = [];
                _.map(rooms, function(room) {
                    warningMsgRooms.push("'{0}' for more than {1} days".format(room.name, room.booking_limit_days));
                });
                var warningMsg = $T.gettext("It is not possible to book room {0}").format(warningMsgRooms.join(", "));
                $('.booking-limit-room-warning .message-text').html(warningMsg);
            }
            $('.booking-limit-room-warning').toggleClass('hidden', !rooms.length);
        }

        var validEndDates = null;
        var frequencies = {
            '1' : RRule.DAILY,
            '2' : RRule.WEEKLY,
            '3' : RRule.MONTHLY
        };

        $('#timerange').timerange({
            initStartTime: '${ form.start_dt.data.strftime("%H:%M") }',
            initEndTime: '${ form.end_dt.data.strftime("%H:%M") }',
            startTimeName: 'sTime',
            endTimeName: 'eTime',
            sliderWidth: '512px',
            change: function() {
                combineDatetime();
                validateForm();
            }
        });

        $('#sDatePlace, #eDatePlace').datepicker({
            dateformat: 'dd/mm/yy',
            % if not can_override:
                maxDate: ${ room.max_advance_days - 1 if room and room.max_advance_days else 'null' },
            % endif
            showButtonPanel: true,
            changeMonth: true,
            changeYear: true,
            showOn: 'focus',
            unifyNumRows: true
        });

        % if not can_override:
            $('#sDatePlace').datepicker('option', 'minDate', ${ "'{}'".format(min(min_date, form.start_dt.data).strftime('%d/%m/%Y')) if min_date else 0 });
            $('#eDatePlace').datepicker('option', 'minDate', ${ "'{}'".format(min_date.strftime('%d/%m/%Y')) if min_date else 0 });
        % endif

        $('#eDatePlace').datepicker('option', 'beforeShowDay', function validateDate(date) {
            if (validEndDates === null) {
                return [true, '', ''];
            }
            return [validEndDates.indexOf(date.getTime()) !== -1, '', ''];
        });

        $('#sDatePlace').datepicker('option', 'onSelect', function startDateOnSelect(selectedDateText) {
            disableInvalidDays();
            refreshDatePicker($('#eDatePlace'));
            selectEndDate();
            commonOnSelect();
            checkBookingLimit();
        });

        $('#eDatePlace').datepicker('option', 'onSelect', function() {
            commonOnSelect();
            checkBookingLimit();
        });

        $('#eDatePlace').datepicker('option', 'onChangeMonthYear', disableInvalidDays);

        $('#sDatePlace').datepicker('setDate', "${ form.start_dt.data.strftime('%d/%m/%Y') }");
        $('#eDatePlace').datepicker('setDate', "${ form.end_dt.data.strftime('%d/%m/%Y') }");

        $('#repeatability input:radio[name=repeat_frequency]').change(function() {
            checkFrequency();
        });

        $('#roomselector').on('click', '.ui-multiselect-checkboxes :checkbox, .ui-multiselect-all, .ui-multiselect-none', function() {
            checkBookingLimit();
        });

        checkFrequency();
        checkHolidays();

        % if not can_override:
            % if form.start_dt.data < datetime.now():
                $('#timerange').timerange('disable');
                var startDate = moment($('#sDatePlace').datepicker('getDate')).format('D/MM/YYYY');
                // Disable the datea in calendar as well as the calendar itself...
                $('#sDatePlace').datepicker('option', 'beforeShowDay', function validateDate(date) {
                    return [moment(date).format('D/MM/YYYY') == startDate, '', ''];
                });
                $('#sDatePlace').datepicker('disable');
            % endif
            % if form.end_dt.data < datetime.now():
                var endDate = moment($('#eDatePlace').datepicker('getDate')).format('D/MM/YYYY');
                // Disable the datea in calendar as well as the calendar itself...
                $('#eDatePlace').datepicker('option', 'beforeShowDay', function validateDate(date) {
                    return [moment(date).format('D/MM/YYYY') == endDate, '', ''];
                });
                $('#eDatePlace').datepicker('disable');
                $('#repeatability > input[name=repeat_frequency]').not(':checked').prop('disabled', true);
            % endif
        % endif

    });
</script>
