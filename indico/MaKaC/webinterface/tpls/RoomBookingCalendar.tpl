<h2 class="page-title">
    ${ _('Calendar') }
</h2>

<div id="roomBookingCal" ></div>

<script>
    var roomBookingCalendar = new RoomBookingCalendar(
        ${ bars | n, j },
        ${ day_attrs | n, j },
        ${ day_limit | n, j },
        ${ overload | n, j },
        {
            prevURL: ${ prevURL | n, j },
            nextURL: ${ nextURL | n, j },
            startD: ${ startD | n, j },
            endD: ${ endD | n, j },
            periodName: ${ periodName | n, j },
        },
        ${ multiple_rooms | n, j }
    );
    $E('roomBookingCal').set(roomBookingCalendar.draw());
    roomBookingCalendar.addRepeatabilityBarsHovers();
</script>
