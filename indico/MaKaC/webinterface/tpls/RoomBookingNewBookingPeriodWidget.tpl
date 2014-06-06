<%page args="form=None, flexibility=False"/>

<!-- Slider -->
<div id="timerange"></div>

<!-- Repeatibility options -->
<div class="toolbar thin">
    <div id="repeatability" class="group i-selection">
        <span class="i-button label">${ _('Frequency') }</span>
        % for option in form.repeat_unit:
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
<div>
    <div id="sDatePlaceDiv" class="bookDateDiv" style="clear: both;">
        <div id="sDatePlaceTitle" class="label">${ _('Booking date') }</div>
        <div id="sDatePlace"></div>
    </div>
    <div id="eDatePlaceDiv" class="bookDateDiv" style="display:none;">
        <div id='eDatePlaceTitle' class='label'>${ _('End date') }</div>
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
    </div>
</div>

${ form.start_date(type='hidden') }
${ form.end_date(type='hidden') }
${ form.repeat_step(type='hidden') }

<script>
    $(document).ready(function() {
        $('#timerange').timerange({
            initStartTime: '${ format_time(form.start_date.data) }',
            initEndTime: '${ format_time(form.end_date.data) }',
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
                minDate: 0,
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

                combineDatetime();
                checkHolidays();
                validateForm();
            }
        });

        $('#sDatePlace').datepicker('setDate', "${ format_date(form.start_date.data, format='short') }");
        $('#eDatePlace').datepicker('setDate', "${ format_date(form.end_date.data, format='short') }");

        $("#repeatability input:radio[name=repeat_unit]").change(function() {
            if ($(this).val() === '0') {
                $('#sDatePlaceTitle').text("${ _('Booking date') }");
                $('#eDatePlaceDiv').hide();
            } else {
                $('#sDatePlaceTitle').text("${_('Start date')}");
                $('#eDatePlaceDiv').show();
            }

            if ($(this).val() == '1') {
                $("#flexibleDates input:radio").prop("disabled", true);
            } else {
                $("#flexibleDates input:radio").prop("disabled", false);
            }

            if ($(this).val() === '0') {
                $('#repeat_step').val(0);
            } else {
                $('#repeat_step').val(1);
            }
        });

        function combineDatetime() {
            var start_date = moment($('#sDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var end_date = moment($('#eDatePlace').datepicker('getDate')).format('D/MM/YYYY');
            var start_time = $('#timerange').timerange('getStartTime');
            var end_time = $('#timerange').timerange('getEndTime');


            $('#start_date').val('{0} {1}'.format(start_date, start_time));
            $('#end_date').val('{0} {1}'.format(end_date, end_time));
        }

        function checkHolidays() {
            var data = {};
            var repeat_unit = $('input[name=repeat_unit]:checked').val();

            data.start_date = moment($('#start_date').val(), 'D/MM/YYYY H:m').format('YYYY-MM-D');
            if (repeat_unit !== '0') {
                data.end_date = moment($('#end_date').val(), 'D/MM/YYYY H:m').format('YYYY-MM-D')
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

        checkHolidays();
    });
</script>
