<script type="text/javascript">

    var userId = "rb-user-${user.getId() if user else 'not-logged'}";
    var rbUserData = $.jStorage.get(userId, {});
    var maxRoomCapacity = ${maxRoomCapacity};

    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function validateForm(onlyLocal) {

        // Clean up - make all textboxes white again
        var searchForm = $('#searchForm');
        $(':input', searchForm).removeClass('invalid');

        // Init
        var isValid = true;

        if (!$("#roomselector").roomselector("validate")) {
          isValid = false;
        }

        // Holidays warning
        if (!onlyLocal) {
            saveCalendarData($('#finishDate').val());
            var holidaysWarning = indicoSource('roomBooking.getDateWarning', searchForm.serializeObject());
            holidaysWarning.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    $('#holidays-warning').html(holidaysWarning.get());
                    if (holidaysWarning.get() == '')
                        $('#holidays-warning').hide();
                    else
                        $('#holidays-warning').show();
                }

            });
        }

        // Flexible date range
        if ($("#flexibleDates").is(':checked')) {
            var sdate = new Date($('#sYear').val(), parseInt($('#sMonth').val() - 1), $('#sDay').val());
            var edate = new Date($('#eYear').val(), parseInt($('#eMonth').val() - 1), $('#eDay').val());
            sdate.setDate(sdate.getDate() - parseInt($('#flexibleDatesRange').val()));
            edate.setDate(edate.getDate() + parseInt($('#flexibleDatesRange').val()));
            $('#sDay').val(sdate.getDate());
            $('#sMonth').val(parseInt(sdate.getMonth() + 1));
            $('#sYear').val(sdate.getFullYear());
            $('#eDay').val(edate.getDate());
            $('#eMonth').val(parseInt(edate.getMonth() + 1));
            $('#eYear').val(edate.getFullYear());
        }

        // Date validator (repeatability)
        if ($('#repeatability').val() != 'None') {
            isValid = validate_period(true, true, 1) && isValid; // 1: validate dates
        }

        // Time validator
        if ($('#sTime').val() != '') {
            isValid = validate_period(false, false, 2) && isValid; // 2: validate only times
        }

        return isValid;
    }

    $(window).on('load', function() {

        $("#roomselector").roomselector({rooms: ${rooms | j, n},
                                         roomMaxCapacity: maxRoomCapacity,
                                         rbUserData: rbUserData});

        // Calendars init
        $("#sDatePlace, #eDatePlace").datepicker({
            defaultDate: null,
            minDate: 0,
            firstDay: 1,
            showButtonPanel: true,
            changeMonth: true,
            changeYear: true,
            numberOfMonths: 1,
            onSelect: function( selectedDate ) {
                if ($("#sDatePlace").datepicker('getDate') > $("#eDatePlace").datepicker('getDate')) {
                    $("#eDatePlace").datepicker('setDate', $("#sDatePlace").datepicker('getDate'));
                }
                validateForm(false);
            }
        });

        // Default date
        % if today.day != '':
            $("#sDatePlace").datepicker('setDate', new Date (${ today.year } + "/" + ${ today.month } + "/" + ${ today.day }));
            $("#eDatePlace").datepicker('setDate', new Date (${ today.year } + "/" + ${ today.month } + "/" + ${ today.day }));
        % endif

        // Restore saved form data
        if (rbUserData.sDay) {
            $("#sDatePlace").datepicker('setDate', new Date (rbUserData.sYear + "/" + rbUserData.sMonth + "/" + rbUserData.sDay));
            $("#eDatePlace").datepicker('setDate', new Date (rbUserData.eYear + "/" + rbUserData.eMonth + "/" + rbUserData.eDay));
        }
        if (rbUserData.sTime) {
            $("#sTime").val(rbUserData.sTime);
            $("#eTime").val(rbUserData.eTime);
        } else  {
            $("#sTime").val("8:30");
            $("#eTime").val("17:30");
        }

        $("#finishDate").val(rbUserData.finishDate);
        $("#flexibleDates").prop('checked', rbUserData.flexibleDates);
        if (rbUserData.flexibleDatesRange) {
            $("#flexibleDatesRange").val(rbUserData.flexibleDatesRange);
        }
        if (rbUserData.repeatability) {
            $("#repeatability").val(rbUserData.repeatability);
        }

        // Time slider init
        $('#timeRange').slider({
            range: true,
            max: 1439,
            values: [510, 1050],
            step: 5,
            create: function(event, ui) {
                updateTimeSlider(event,ui);

            },

            start: function(event, ui) {
                updateTimeSlider(event,ui);
            },

            slide: function(event, ui) {
                validateForm(false);
                updateTimeSlider(event,ui);
            }
          });

        // CSS and text
        $('#flexibleDatesRange').prop('disabled', !$("#flexibleDates").prop('checked'));
        if ($("#finishDate").val() == 'true')
            $('#eDatePlaceDiv').show();

        // Listeners
        $('#searchForm').delegate(':input', 'change keyup', function() {
            if (validateForm(false)){
                $("#roomselector").roomselector("update");
                updateTimeSlider();
            }
        }).submit(function(e) {
            saveFormData();
            if (!validateForm(true)) {
                new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
                e.preventDefault();
            }
            else if($("#roomselector").roomselector("value") === null) {
                new AlertPopup($T("Error"), $T("Please select a room (or several rooms)..")).open();
                e.preventDefault();
            }
        });

        $('#repeatability').change(function() {
            if ($(this).val() != 'None') {
                $('#sDatePlaceTitle').text('${ _("Start date")}');
                $('#finishDate').val('true');
                $('#eDatePlaceDiv').show();
            } else {
                $('#sDatePlaceTitle').text('${ _("Booking date")}');
                $('#finishDate').val('false');
                $('#eDatePlaceDiv').hide();
            }
            if ($(this).val() == '0') {
                $('#flexibleDatesDiv').hide();
                $('#flexibleDates').prop('checked', false);
            } else {
                $('#flexibleDatesDiv').show();
            }

        });

        $('#repeatability').change();

        $('#flexibleDates').on('change', function() {
            $('#flexibleDatesRange').prop('disabled', !this.checked);
        });
 });
</script>

<form id="searchForm" method="post" action="${ roomBookingBookingListURL }">
    <table id="roomBookingTable" style="width: 100%; padding-left: 20px;">
        <tr>
            <td>
                <ul id="breadcrumbs" style="margin:0px 0px 0px -15px; padding: 0; list-style: none;">
                    <li><span class="current">${_("Specify Search Criteria")}</span></li>
                    <li><span>${_("Select Available Period")}</span></li>
                    <li><span>${_("Confirm Reservation")}</span></li>
                </ul>
            </td>
        </tr>
        <tr>
            <td>
                <h2 class="group_title">
                    <i class="icon-location"></i>
                    ${_("Rooms")}
                </h2>
            </td>
        </tr>
        <!-- ROOMS -->
        <tr>
          <td>
              <div id="roomselector"></div>
           </td>
        </tr>
        <!-- DATES -->
        <tr>
            <td>
                <h2 class="group_title">
                    <i class="icon-calendar"></i>
                    ${_("Date range")}
                </h2>
            </td>
        </tr>
        <tr>
            <td style="text-align: center;" >
                <div style="float: left; clear: both; padding-bottom: 30px;">
                    ${ _("Type")}
                    <select name="repeatability" id="repeatability" style=" width: 230px;">
                        <option value="None"> ${ _("Single reservation")}</option>
                        <option value="0"> ${ _("Repeat daily")}</option>
                        <option value="1"> ${ _("Repeat once a week")}</option>
                        <option value="2"> ${ _("Repeat once every two weeks")}</option>
                        <option value="3"> ${ _("Repeat once every three weeks")}</option>
                        <option value="4"> ${ _("Repeat every month")}</option>
                    </select>
                </div>
                <div id="sDatePlaceDiv" class="titleCellFormat bookDateDiv" style="clear: both;" >
                    <span id='sDatePlaceTitle' class='label'>${ _("Booking date")}</span>
                    <div id="sDatePlace"></div>
                </div>
                <div id="eDatePlaceDiv" class="titleCellFormat bookDateDiv" style="display: none;" >
                    <span id='eDatePlaceTitle' class='label'>${ _("End date")}</span>
                    <div id="eDatePlace"></div>
                </div>
                <div class="infoMessage" id="holidays-warning" style="float: left; display: none"></div>
                <div id="flexibleDatesDiv" style="float: left; clear: both; ">
                    <input name="flexibleDates" type="checkbox" id="flexibleDates" />
                   ${ _("Flexible on dates") }
                    <select name="flexibleDatesRange" id="flexibleDatesRange">
                      <option value="1">${ _("+/- 1 day")}</option>
                      <option value="2">${ _("+/- 2 days")}</option>
                      <option value="3">${ _("+/- 3 days")}</option>
                    </select>
                </div>
                <input name="finishDate" id="finishDate" type="hidden" />
                <input name="sDay" id="sDay" type="hidden" />
                <input name="sMonth" id="sMonth" type="hidden" />
                <input name="sYear" id="sYear" type="hidden" />
                <input name="eDay" id="eDay" type="hidden" />
                <input name="eMonth" id="eMonth"  type="hidden" />
                <input name="eYear" id="eYear" type="hidden" />
            </td>
        </tr>
        <!-- TIME -->
        <tr>
            <td>
                <h2 class="group_title">
                    <i class="icon-time"></i>
                    ${ _("Time range") }
                </h2>
            </td>
        </tr>
        <tr>
            <td>
                ${ _("Booking time from")}
                <input name="sTime" id="sTime" style="width: 43px;" type="text" />
                ${ _("to")}
                <input name="eTime" id="eTime" style="width: 43px;" type="text" />
            </td>
        </tr>
        <!-- TIME SLIDER-->
        <tr>
            <td>
                <div style="margin: 13px 0px 32px 0px; padding-top: 10px;">
                    <div id="minHour" style="float: left; color: gray; padding-right: 12px">0:00</div>
                    <div id="timeRange" style="width: 390px; float: left;"></div>
                    <div id="maxHour" style="float: left; color: gray; padding-left: 12px">23:59</div>
                    <div id="sTimeBubble" style="position: absolute; margin: -19px 0px 0px -8px;">&nbsp;</div>
                    <div id="eTimeBubble" style="position: absolute; margin: 20px 0px 0px -8px;">&nbsp;</div>
                </div>
            </td>
        </tr>
        <!-- SUBMIT BUTTON -->
        <tr>
            <td>
                <div class="groupTitle bookingTitle"></div>
            </td>
        </tr>
        <tr>
            <td>
                <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                  <li class="button" onclick="$('#searchForm').submit(); return false;">
                    <a href="#" >${ _('Search')}</a>
                  </li>
                  <li style="display: none"></li>
                </ul>
                <span style="float: right;"><a href=${quoteattr(str(urlHandlers.UHRoomBookingSearch4Rooms.getURL( forNewBooking = True )))}>${_("Former booking interface")}</a></span>
            </td>
        </tr>
    </table>
</form>
