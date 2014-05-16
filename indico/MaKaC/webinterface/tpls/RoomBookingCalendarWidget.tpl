% if can_navigate:
    % if not form_data:
        <form id="room-booking-calendar-form" method="GET">
            <input type="hidden" name="start_date" value="${ start_dt.date().strftime('%d/%m/%Y') }">
            <input type="hidden" name="end_date" value="${ end_dt.date().strftime('%d/%m/%Y') }">
        </form>
    % else:
        <form id="room-booking-calendar-form" method="POST">
            % for name, values in form_data.iterlists():
                % for value in values:
                    <input type="hidden" name="${ name }" value="${ value }">
                % endfor
            % endfor
        </form>
    % endif
% endif

<div id="roomBookingCal"></div>
<script>
    var roomBookingCalendar = new RoomBookingCalendar({
        bars: ${ bars | n, j },
        dayAttrs: ${ days | n, j },
        firstDay: ${ start_dt.date().strftime('%Y-%m-%d') | n, j },
        lastDay: ${ end_dt.date().strftime('%Y-%m-%d') | n, j },
        specificRoom: ${ specific_room | n, j },
        repeatUnit: ${ repeat_unit | n, j },
        flexibleDays: ${ flexible_days | n, j },
        rejectAllLink: '',
        showSummary: ${ show_summary | n, j },
        showNavBar: ${ show_navbar | n, j },
        canNavigate: ${ can_navigate | n, j }
    });

    $E('roomBookingCal').set(roomBookingCalendar.draw());
    roomBookingCalendar.addRepeatabilityBarsHovers();
</script>
