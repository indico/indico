<%page args="form=None, flexibility=False, can_override=False, min_date=None, date_changed=None, past_date=None"/>

<!-- Slider -->
<div id="timerange"></div>

<!-- Repeatibility options -->
<div class="toolbar thin">
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
                    ${ _('This room can only be booked {0} days in advance'.format(room.max_advance_days)) }
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
    </div>
</div>

${ form.start_dt(type='hidden') }
${ form.end_dt(type='hidden') }
${ form.repeat_interval(type='hidden') }

<script>
    $(document).ready(function() {
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
                minDate: ${ "'{}'".format(min_date.strftime('%d/%m/%Y')) if min_date else 0 },
                maxDate: ${ room.max_advance_days - 1 if room and room.max_advance_days else 'null' },
            % endif
            showButtonPanel: true,
            changeMonth: true,
            changeYear: true,
            showOn: 'focus',
            onSelect: function(selectedDate) {
                if ($('#sDatePlace').datepicker('getDate') > $('#eDatePlace').datepicker('getDate')) {
                    $('#eDatePlace').datepicker('setDate', $('#sDatePlace').datepicker('getDate'));
                }
                $('#eDatePlace').datepicker('option', 'minDate', $('#sDatePlace').datepicker('getDate'));
                $('.js-default-date-warning').fadeOut();
                combineDatetime();
                checkHolidays();
                validateForm();
            }
        });

        $('#sDatePlace').datepicker('setDate', "${ form.start_dt.data.strftime('%d/%m/%Y') }");
        $('#eDatePlace').datepicker('setDate', "${ form.end_dt.data.strftime('%d/%m/%Y') }");
        $('#eDatePlace').datepicker('option', 'minDate', $('#sDatePlace').datepicker('getDate'));

        $("#repeatability input:radio[name=repeat_frequency]").change(function() {
            checkFrequency();
        });

        function checkFrequency() {
            var frequency = $("#repeatability input:radio[name=repeat_frequency]:checked").val();

            if (frequency === '0') {
                $('#sDatePlaceTitle').text("${ _('Booking date') }");
                $('#eDatePlaceDiv').hide();
            } else {
                $('#sDatePlaceTitle').text("${_('Start date')}");
                $('#eDatePlaceDiv').show();
            }

            if (frequency == '1') {
                $("#flexibleDates input:radio").prop("disabled", true);
            } else {
                $("#flexibleDates input:radio").prop("disabled", false);
            }

            if (frequency === '0') {
                $('#repeat_interval').val(0);
            } else {
                $('#repeat_interval').val(1);
            }
        }

        function combineDatetime() {
            var start_date = moment($('#sDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var end_date = moment($('#eDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var start_time = $('#timerange').timerange('getStartTime');
            var end_time = $('#timerange').timerange('getEndTime');


            $('#start_dt').val('{0} {1}'.format(start_date, start_time));
            $('#end_dt').val('{0} {1}'.format(end_date, end_time));
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

        checkFrequency();
        checkHolidays();
    });
</script>
