<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <li><span class="current">${ _('Specify Search Criteria') }</span></li>
    <li><span>${ _('Select Available Period') }</span></li>
    <li><span>${ _('Confirm Reservation') }</span></li>
</ul>

<%include file="ErrorList.tpl" args='errors=errors, msg=_("There are some errors in the search criteria:")'/>

<form id="searchForm" method="POST" action="">
    <input type="hidden" name="step" value="1">

    <h2 class="group-title">
        <i class="icon-location"></i>
        ${ _('Rooms') }
    </h2>
    <div id="roomselector"></div>

    <h2 class="group-title">
        <i class="icon-time"></i>
        ${ _('Booking time & date') }
    </h2>
    <%include file="RoomBookingNewBookingPeriodWidget.tpl" args="form=form, flexibility=True"/>

    <h2 class="group-title"></h2>
    <button type="submit" class="i-button highlight">${ _('Continue') }</button>
</form>

<script>
    var userId = "rb-user-${ user.getId() if _session.user else 'not-logged' }";
    var rbUserData = $.jStorage.get(userId, {});
    var maxRoomCapacity = ${ max_room_capacity };
    var rooms = ${ [r.to_serializable('__public_exhaustive__') for r in rooms] | j, n };

    $(document).ready(function() {
        initWidgets();
        restoreUserData();

        function initWidgets() {
            $('#roomselector').roomselector({
                allowEmpty: false,
                rooms: rooms,
                roomMaxCapacity: maxRoomCapacity,
                userData: rbUserData,
                selectName: '${ form.room_ids.name }'
            });
        }

        function restoreUserData() {
            if (rbUserData.startDate) {
                $("#sDatePlace").datepicker('setDate', moment(rbUserData.startDate).toDate());
            }
            if (rbUserData.endDate) {
                $("#eDatePlace").datepicker('setDate', moment(rbUserData.endDate).toDate());
            }

            $("#finishDate").val(rbUserData.finishDate);
            $("input[name=repeat_unit][value=" + rbUserData.repeatUnit + "]").prop('checked', true).change();
            $("#flexibleDates input[name=flexible_dates_range][value=" + rbUserData.flexibleDatesRange + "]").prop('checked', true);

            if (rbUserData.startTime && rbUserData.endTime) {
                $('#timerange').timerange('setStartTime', rbUserData.startTime).timerange('setEndTime', rbUserData.endTime);
            }
        }
    });
</script>
