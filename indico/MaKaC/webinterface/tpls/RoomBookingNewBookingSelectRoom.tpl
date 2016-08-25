<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <li><span class="current">${ _('Specify Search Criteria') }</span></li>
    <li><span>${ _('Select Available Period') }</span></li>
    <li><span>${ _('Confirm Reservation') }</span></li>
</ul>

<%include file="ErrorList.tpl" args='errors=errors, msg=_("There are some errors in the search criteria")'/>

<form id="searchForm" method="POST" action="">
    ${ form.csrf_token() }
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
    var userId = "rb-user-${ _session.user.id if _session.user else 'not-logged' }";
    var rbUserData = $.jStorage.get(userId, {});
    var maxRoomCapacity = ${ max_room_capacity };
    var rooms = ${ serializable_rooms | j, n };
    var myRooms = ${ my_rooms | j, n };

    $(document).ready(function() {
        initWidgets();
        % if not ignore_userdata:
            restoreUserData();
        % endif

        function initWidgets() {
            $('#roomselector').roomselector({
                allowEmpty: false,
                rooms: rooms,
                myRooms: myRooms,
                roomMaxCapacity: maxRoomCapacity,
                userData: ${ 'rbUserData' if not ignore_userdata else {}},
                selectName: '${ form.room_ids.name }',
                selectedRooms: ${ form.room_ids.data | j, n }
            });
        }

        function restoreUserData() {
            if (rbUserData.startDate) {
                var savedStartDate = moment(rbUserData.startDate).toDate();
                if ($('#sDatePlace').datepicker('getDate').getTime() != savedStartDate.getTime()) {
                    $('.js-default-date-warning').hide();
                }
                $('#sDatePlace').datepicker('setDate', savedStartDate);
            }
            if (rbUserData.endDate) {
                $("#eDatePlace").datepicker('setDate', moment(rbUserData.endDate).toDate());
            }

            $("#finishDate").val(rbUserData.finishDate);
            $("input[name=repeat_frequency][value=" + rbUserData.repeatFrequency + "]").prop('checked', true).change();
            $("#flexibleDates input[name=flexible_dates_range][value=" + rbUserData.flexibleDatesRange + "]").prop('checked', true);

            if (rbUserData.startTime && rbUserData.endTime) {
                $('#timerange').timerange('setStartTime', rbUserData.startTime).timerange('setEndTime', rbUserData.endTime);
            }
        }
    });
</script>
