<h2 class="page-title">
    ${ _('Search bookings') }
</h2>

<%include file="ErrorList.tpl" args='errors=errors, msg=_("There are some errors in the search criteria")'/>

<form method="post" action="" id="searchBookings">
    ${ form.csrf_token() }
    <h2 class="group-title">
        <i class="icon-location"></i>
        ${ _('Taking place in') }
    </h2>

    <div id="roomselector"></div>

    <div id="timespan">
        <h2 class="group-title">
            <i class="icon-time"></i>
            ${ _('Timespan') }
        </h2>

        <div class="toolbar thin space-after">
            <div class="group with-datepicker">
                <span class="i-button label heavy">
                    ${ _('Start Date') }
                </span>
                <span class="datepicker thin">
                    <input type="text" name="start_date" id="start_date"/>
                </span>
            </div>

            <div class="group right with-datepicker">
                <span class="i-button label heavy">
                    ${ _('End Date') }
                </span>
                <span class="datepicker thin">
                    <input type="text" name="end_date" id="end_date"/>
                </span>
            </div>
        </div>
        <div id="timerange"></div>
    </div>

    <div id="bookingDetails">
        <h2 class="group-title">
            <i class="icon-info"></i>
            ${ _('Booking details') }
        </h2>

        <div class="toolbar thin space-after">
            <div class="group">
                <span class="i-button label">
                    ${ _('Booked for') }
                </span>
                <input size="30" type="text" id="booked_for_name" name="booked_for_name"
                    placeholder="${ _('Enter name...') }" />
            </div>
        </div>
        <div class="toolbar thin space-after">
            <div class="group">
                <span class="i-button label">
                    ${ _('Reason') }
                </span>
                <input size="30" type="text" id="reason" name="reason"
                    placeholder="${ _('Enter reason...') }"/>
            </div>
        </div>

        <div class="toolbar thin space-after table">
            <div class="group i-selection">
                <span class="i-button label">
                    ${ _('Booked') }
                </span>
                <input type="radio" id="any_booker" name="is_only_mine" value="false" checked/>
                <label for="any_booker" class="i-button"
                    title="${ _('Shows all bookings') }">
                    ${ _('Anyone') }
                </label>
                <input type="radio" id="only_mine" name="is_only_mine" value="true"/>
                <label for="only_mine" class="i-button"
                    title="${ _('Filter by your bookings') }">
                    ${ _('Me') }
                </label>
            </div>
        </div>

        <div class="toolbar thin space-after table">
            <div class="group i-selection">
                <span class="i-button label">
                    ${ _('Type') }
                </span>
                <input type="checkbox" id="is_only_bookings" name="is_only_bookings"/>
                <label for="is_only_bookings" class="i-button"
                    title="${ _('Filter by confirmed bookings') }">
                    ${ _('Bookings') }
                </label>
                <input type="checkbox" id="is_only_pre_bookings" name="is_only_pre_bookings"/>
                <label for="is_only_pre_bookings" class="i-button"
                    title="${ _('Filter by pre-bookings') }">
                    ${ _('Pre-Bookings') }
                </label>
            </div>
        </div>

        <div class="toolbar thin space-after table">
            <div class="group i-selection">
                <span class="i-button label">
                    ${ _('State') }
                </span>
                <input type="checkbox" id="is_rejected" name="is_rejected"/>
                <label for="is_rejected" class="i-button"
                    title="${ _('Filter by rejected bookings') }">
                    ${ _('Rejected') }
                </label>
                <input type="checkbox" id="is_cancelled" name="is_cancelled"/>
                <label for="is_cancelled" class="i-button"
                    title="${ _('Filter by cancelled bookings') }">
                    ${ _('Cancelled') }
                </label>
                <input type="checkbox" id="is_archived" name="is_archived"/>
                <label for="is_archived" class="i-button"
                    title="${ _('Filter by archived bookings') }">
                    ${ _('Archived') }
                </label>
            </div>
        </div>

        <div class="toolbar thin space-after table">
            <div class="group i-selection">
                <span class="i-button label">
                    ${ _('Services') }
                </span>
                <input type="checkbox" id="uses_vc" name="uses_vc"/>
                <label for="uses_vc" class="i-button"
                    title="${ _('Filter by bookings which will use videoconference systems') }">
                    ${ _('Videoconference') }
                </label>
            </div>
        </div>

        <div class="toolbar thin table">
            <div class="group i-selection">
                <span class="i-button label">
                    ${ _('Assistance') }
                </span>
                <input type="checkbox" id="needs_vc_assistance" name="needs_vc_assistance"/>
                <label for="needs_vc_assistance" class="i-button"
                    title="${ _('Filter by bookings which requested assistance for the startup of the videoconference session') }">
                    ${ _('Videoconference') }
                </label>
                <input type="checkbox" id="needs_assistance" name="needs_assistance"/>
                <label for="needs_assistance" class="i-button"
                    title="${ _('Filter by bookings which requested assistance for the startup of the meeting') }">
                    ${ _('Startup') }
                </label>
            </div>
        </div>
    </div>

    <h2 class="group-title"></h2>
    <div class="submit-button-wrapper">
        <button type="send" class="i-button highlight">
            <i class="icon-search"></i>
            <span>
                ${ _('Search') }
            </span>
        </button>
    </div>
</form>

<script>
    var userId = "rb-user-${ user.getId() if _session.user else 'not-logged' }";
    var userData = "search-form-" + userId;
    var rbUserData = $.jStorage.get(userData, {});
    var rooms = ${ [r.to_serializable('__public_exhaustive__') for r in rooms] | j, n };
    var myRooms = ${ my_rooms | j, n };

    $(document).ready(function() {
        initWidgets();
        % if not ignore_userdata:
            restoreSearchData();
        % endif

        function adjustDates(s, e) {
            if (s.datepicker('getDate') > e.datepicker('getDate'))
                e.datepicker('setDate', s.datepicker('getDate'));
        }

        function initWidgets() {
            $('#roomselector').roomselector({
                allowEmpty: false,
                rooms: rooms,
                myRooms: myRooms,
                userData: ${ 'rbUserData' if not ignore_userdata else {}},
                selectName: 'room_ids',
                simpleMode: true
            });

            $('#timerange').timerange({
                sliderWidth: '320px'
            });

            var s = $('#start_date'), e = $('#end_date');
            $('#start_date, #end_date').datepicker({
                onSelect: function() {
                    adjustDates(s, e);
                    $('#searchBookings').trigger('change');
                }
            });
            s.datepicker('setDate', '+0');
            e.datepicker('setDate', '+6');
        }

        function restoreSearchData() {
            if (rbUserData.startDate) {
                $('#start_date').datepicker('setDate', moment(rbUserData.startDate).toDate());
            }
            if (rbUserData.endDate) {
                $('#end_date').datepicker('setDate', moment(rbUserData.endDate).toDate());
            }

            $('input[name=booked_for_name]').val(rbUserData.bookedFor);
            $('input[name=reason]').val(rbUserData.reason);
            $('input[name=is_only_mine][value=' + rbUserData.booker + ']').prop('checked', true).change();
            $('input[name=is_only_bookings]').prop('checked', rbUserData.typeBookings);
            $('input[name=is_only_pre_bookings]').prop('checked', rbUserData.typePreBookings);
            $('input[name=is_rejected]').prop('checked', rbUserData.stateRejected);
            $('input[name=is_cancelled]').prop('checked', rbUserData.stateCanceled);
            $('input[name=is_archived]').prop('checked', rbUserData.stateArchived);
            $('input[name=uses_vc]').prop('checked', rbUserData.service);
            $('input[name=needs_vc_assistance]').prop('checked', rbUserData.assistVc);
            $('input[name=needs_assistance]').prop('checked', rbUserData.assistStartup);

            if (rbUserData.startTime && rbUserData.endTime) {
                $('#timerange').timerange('setStartTime', rbUserData.startTime).timerange('setEndTime', rbUserData.endTime);
            }
        }
    });
</script>
