<script type="text/javascript">

    var userId = "rb-user-${user.getId() if user else 'not-logged'}";

    var maxRoomCapacity = 0;

    % if rooms:
        var maxRoomCapacity = ${ max(room.capacity for room in rooms) };
    % endif

    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function validateForm(onSubmit) {

        // Clean up - make all textboxes white again
        var searchForm = $('#searchForm');
        $(':input', searchForm).removeClass('invalid');

        // Init
        var isValid = true;

        // Capacity validator
        var capacity = $('#capacity').val();
        if (capacity != '' && (capacity < 0 || capacity > maxRoomCapacity || parseInt(capacity, 10).toString() == 'NaN')) {
            capacity.addClass('invalid');
            isValid = false;
        }

        // Holidays warning
        if (!onSubmit) {
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

    $(window).load(function() {

        // Multiselect widget init
        $('#roomGUID').multiselect({
            height: 255,
            minWidth: 490,
            checkAllText: 'All',
            uncheckAllText: 'None',
            noneSelectedText: '0 selected',
            autoOpen: true,
            beforeclose: function (event, ui) {
                return false;
            },
            classes : "RoomBooking",
        }).multiselectfilter({
            label: "",
            placeholder: "",
        });

        $("#roomGUID").bind("multiselectclick", function(event, ui) {
            changeSelectedStyle($('.RoomBooking.ui-multiselect-menu input[value="' + ui.value + '"]'));
            updateSelectionCounter();
        });

        $("#roomGUID").bind("multiselectcheckall", function(event, ui) {
            changeSelectedStyleAll();
        });

        $("#roomGUID").bind("multiselectuncheckall", function(event, ui) {
            changeSelectedStyleAll();
        });

        $("#roomGUID").multiselect("widget").bind( {
            mouseleave: function(){
                $("#roomGUID").multiselect("widget").find('label').removeClass('ui-state-hover');
            },
        });

        $("#roomGUID").bind("multiselectrefresh", function(event, ui) {

           // Header modifications
           var o = $("#roomGUID").multiselect("option");
           var menu = $("#roomGUID").multiselect("widget");

           $('.RoomBooking .ui-widget-header .ui-helper-reset').html('<li><span>Select: </span> <a class="ui-multiselect-all" href="#"><span class="ui-icon ui-icon-check"></span><span>' + o.checkAllText + '</span></a></li><li>, <a class="ui-multiselect-none" href="#"><span class="ui-icon ui-icon-close"></span><span>' + o.uncheckAllText + '</span></a>');

           $('<div />').addClass('ui-multiselect-search-advanced')
                .html(function(){
                    return '<span id="advancedOptionsText" style="float: right; padding: 2px 10px 0px 20px" >&nbsp;</span>';
                }).appendTo( menu.children().first() );

            $('<div />').addClass('ui-multiselect-ui-multiselect-scrollbar-up').insertAfter( menu.children().first() );
            $('<div />').addClass('ui-multiselect-ui-multiselect-scrollbar-down').appendTo( menu );
            $('<div />').addClass('ui-multiselect-selection-counter').appendTo( menu );
            $('<div />').addClass('ui-multiselect-selection-summary').appendTo( menu );

            $('.RoomBooking .ui-multiselect-selection-counter').text(o.selectedText.replace('#', $(".RoomBooking.ui-multiselect-menu input:checked").length));

            // Adding advanced lables
            var advancedImages = ["../images/rb_video.png","../images/rb_webcast.png", "../images/rb_public.png", "../images/rb_capacity.png"];
            var advancedImagesTitles = ["Video conference", "Webcast/Recording", "Public room", "Capacity"];

            $("#roomGUID option").each(function(index) {
                var advLabelsParts = $(this).attr('label').split(":");
                var html = '</br><div style="padding: 4px 0px 0px 20px; color: gray">';
                for (var i = 0; i < advLabelsParts.length; i++){
                    if (advLabelsParts[i] != 'None' && advLabelsParts[i].toLowerCase() !='false'){
                        html += '<img title="' + advancedImagesTitles[i] + '" class="ui-multiselect-images" src="' + advancedImages[i]+  '">';
                        if (advLabelsParts[i].toLowerCase() != "true") {
                            html += advLabelsParts[i];
                        }
                    }
                }
                var label = $('.RoomBooking.ui-multiselect-menu input[value="' + $(this).val() +'"]').next();
                $(label).html(label.text() + html);
            });

            changeSelectedStyleAll();
        });

        $("#roomGUID").bind("multiselectfilterfilter", function(event, matches) {
            $('.RoomBooking .ui-multiselect-selection-summary').text($('.RoomBooking .ui-multiselect-checkboxes li:visible').length + " / " + $(".RoomBooking .ui-multiselect-checkboxes li").length + " items");
            $('.RoomBooking .ui-multiselect-selection-summary').effect("pulsate", { times:1 }, 400);
        });

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

        // Capacity slider init
        $('#capacityRange').slider({
            range: "max",
            min: 0,
            max: maxRoomCapacity,
            value: 1,
            step: 1,
            create: function(event, ui) {
                updateCapacitySlider(event,ui);
            },

            start: function(event, ui) {
                updateCapacitySlider(event,ui);
            },

            slide: function(event, ui) {
                validateForm(false);
                updateCapacitySlider(event,ui);
            },

            stop: function(event, ui) {
                $('#capacity').keyup();
            },
          });

        // Default date
        % if today.day != '':
            $("#sDatePlace").datepicker('setDate', new Date (${ today.year } + "/" + ${ today.month } + "/" + ${ today.day }));
            $("#eDatePlace").datepicker('setDate', new Date (${ today.year } + "/" + ${ today.month } + "/" + ${ today.day }));
        % endif

        // Restore saved form data
        var rbUserData = $.jStorage.get(userId, {});
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

        $("#capacity").val(rbUserData.capacity);
        $("#videoconference").attr('checked',(rbUserData.videoconference));
        $("#webcast").attr('checked',(rbUserData.webcast));
        $("#publicroom").attr('checked',(rbUserData.publicroom));

        $("#finishDate").val(rbUserData.finishDate);
        $("#flexibleDates").attr('checked',(rbUserData.flexibleDates));
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

            },
          });

        restoreSelection(rbUserData.selectedRooms);
        $("#roomGUID").multiselect("refresh");

        // Restore filter and advanced filter
        $('#advancedOptions').toggle(!rbUserData.showAdvancedOptions);
        showAdvancedOptions();

        $('.ui-multiselect-filter :input').val(rbUserData.filter);
        advancedFilter();

        // Set watermarks
        $('.ui-multiselect-filter :input').watermark($T('Search: name, number, location...'));
        $('#capacity').watermark('0');

        // CSS and text
        $("#roomSelectWidgetSpace").height($('.ui-multiselect-menu').height() + 20);
        $("#advancedOptions").css('left', parseInt($('.ui-multiselect-menu').css('left').replace('px','')) + parseInt($('.ui-multiselect-menu').width()) + 'px'  ).css('top', $('.ui-multiselect-menu').css('top') );
        $('#bookingLegend').width($('.ui-multiselect-menu').width());
        $("#advancedOptionsText").addClass('fakeLink');
        $("#maxRoomCapacity").text(maxRoomCapacity);
        $('#flexibleDatesRange').attr('disabled', !$("#flexibleDates").attr('checked'));
        if ($("#finishDate").val() == 'true')
            $('#eDatePlaceDiv').show();

        // Qtips
        $("#publicRoomHelp").qtip({
            content: {
                text: "room that can be booked by anyone without special permissions"
            },
            position: {
                target: 'mouse',
                adjust: { mouse: true, x: 11, y: 13 }
            },
            show: {

            },
        });

        // Listeners
        $('#searchForm').delegate(':input', 'change keyup', function() {
            if (validateForm(false)){
                updateCapacitySlider();
                updateTimeSlider();
            }
        }).submit(function(e) {
            saveFormData();
            if (!validateForm(true)) {
                new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
                e.preventDefault();
            }
            else if($('#roomGUID').val() == null) {
                new AlertPopup($T("Error"), $T("Please select a room (or several rooms)..")).open();
                e.preventDefault();
            }
        });

        $("#advancedOptionsText").click(function () {
            showAdvancedOptions();
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
                $('#flexibleDates').attr('checked', false);
            } else {
                $('#flexibleDatesDiv').show();
            }

        });

        $('#repeatability').change();
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
                <div class="groupTitle bookingTitle">${ _("Choose rooms") }</div>
            </td>
        </tr>
        <!-- ROOMS -->
        <tr>
          <td>
             <div id="roomSelectWidgetSpace">
                <select name="roomGUID" id="roomGUID" multiple="multiple" size="10" style="display: none" >
                    % for room in rooms:
                        <option label="${str(room.needsAVCSetup) + ':' + str(room.hasWebcastRecording()) + ':' + str(room.isReservable and not room.customAtts.get('Booking Simba List')) + ':' + (str(room.capacity) if room.capacity else '0')}" name = "${ str(room.getBookingUrl()) }" value="${ str( room.guid ) }" class="${ roomClass( room ) }">${ room.locationName + " &nbsp; " + room.getFullName()}</option>
                    % endfor
                </select>
             </div>
             <!--  ADVANCED SEARCH -->
             <div id="advancedOptions" style="background-color: #eaeaea; position: absolute; padding: 5px; border-radius: 0px 10px 10px 0px; display: none; ">
                <table>
                    <!-- CAPACITY -->
                    <tr >
                        <td>
                            <img src="../images/rb_capacity.png">
                            <small> ${ _("Minimum capacity")}&nbsp;&nbsp;</small>
                        </td>
                        <td>
                            <input name="capacity" id="capacity" size="3" type="text" value="" style="width: 43px;" onkeyup="advancedFilter();" />
                        </td>
                    </tr>
                    <!-- CAPACITY SLIDER-->
                    <tr>
                        <td colspan="2" >
                            <div id="minRoomCapacity" style="float: left; color: gray; padding-right: 5px">0</div>
                            <div id="capacityRange" style="float: left; width: 100px; margin: 0px 0px 9px 10px;"></div>
                            <div id="maxRoomCapacity"style="float: left; color: gray; padding-left: 12px;"></div>
                        </td>
                    </tr>
                    <!-- VIDEO CONFERENCE -->
                    <tr>
                        <td>
                            <img src="../images/rb_video.png">
                            <small> ${ _("Video conference")}&nbsp;&nbsp;</small>
                        </td>
                        <td>
                            <input name="videoconference" id="videoconference" type="checkbox" onchange="advancedFilter();" />
                        </td>
                    </tr>
                    <!-- WEBCAST/RECORDING -->
                    <tr>
                        <td>
                            <img src="../images/rb_webcast.png">
                            <small> ${ _("Webcast/Recording")}&nbsp;&nbsp;</small>
                        </td>
                        <td>
                            <input name="webcast" id="webcast" type="checkbox" onchange="advancedFilter();" />
                        </td>
                    </tr>
                    <!-- PUBLIC ROOM -->
                    <tr>
                        <td >
                            <img src="../images/rb_public.png">
                            <small> ${ _("Public room")}&nbsp;&nbsp;</small>
                        </td>
                        <td>
                            <input name="publicroom" id="publicroom" type="checkbox" onchange="advancedFilter();" />
                        </td>
                    </tr>
                </table>
             </div>
             <!-- LEGEND -->
             <div id="bookingLegend" style="background: #F2F2F2; border-top: 1px solid #DDD; padding: 5px 0px 3px 0px; margin-top: -9px">
                <!-- CAPACITY -->
                <img src="../images/rb_capacity.png" style="padding-left: 5px;">
                <small> ${ _("Capacity")}&nbsp;&nbsp;</small>
                <!-- VIDEO CONFERENCE -->
                <img src="../images/rb_video.png">
                <small> ${ _("Video conference")}&nbsp;&nbsp;</small>
                <!-- WEBCAST/RECORDING -->
                <img src="../images/rb_webcast.png">
                <small> ${ _("Webcast/Recording")}&nbsp;&nbsp;</small>
                <!-- PUBLIC ROOM -->
                <span id="publicRoomHelp">
                    <img src="../images/rb_public.png">
                    <small> ${ _("Public room")}&nbsp;&nbsp;</small>
                </span>
             </div>
           </td>
        </tr>
        <!-- DATES -->
        <tr>
            <td>
                <div class="groupTitle bookingTitle" style="padding-top: 20px;">${ _("Select date range") }</div>
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
                    <input name="flexibleDates" type="checkbox" id="flexibleDates" onclick="if ($(this).attr('checked')) {$('#flexibleDatesRange').attr('disabled', false);} else {$('#flexibleDatesRange').attr('disabled', true);}" />
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
                <div class="groupTitle bookingTitle" style="padding-top: 30px;">${ _("Select time range") }</div>
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
