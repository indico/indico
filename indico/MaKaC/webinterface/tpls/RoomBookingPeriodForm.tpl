<%page args="repeatability=None, form=None, unavailableDates=None, availableDayPeriods=None, maxAdvanceDays=None"/>
<script type="text/javascript">

    // Comments the repeatition for user, to make it clear
    function set_repeatition_comment() {
        var s = '';
        var repType = parseInt($('#repeatability').val(), 10);
        if(repType > 0) {
            var date = new Date(parseInt($('#sYear').val(), 10), parseInt($('#sMonth').val()-1, 10), parseInt($('#sDay').val(), 10));
            var weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            s = 'on ' + weekDays[date.getDay()];
            if(repType == 4) {
                weekNr = Math.floor( date.getDate() / 7 ) + 1;
                postfix = ['st', 'nd', 'rd', 'th', 'th'];
                weekNrStr = 'the ' + weekNr + postfix[weekNr-1] + ' ';
                s = 'on ' + weekNrStr + weekDays[date.getDay()] + ' of a month';
            }
        }
        $('#repComment').html(s);
    }

    // Converting from time string to seconds
    function getTime(time) {
        var minutes = parseInt(time % 60);
        var hours = parseInt(time / 60 % 24);
        minutes = minutes + "";
        if (minutes.length == 1) {
            minutes = "0" + minutes;
        }
        return hours + ":" + minutes;
    }

    // Refresh time slider
    function updateTimeSlider(event, ui) {
        if (event && event.type != "slidecreate" ) {
            $("#sTime").val(getTime(ui.values[0]));
            $("#eTime").val(getTime(ui.values[1]));
        }
        var sTime = parseInt($("#sTime").val().split(":")[0] * 60) + parseInt($("#sTime").val().split(":")[1]);
        var eTime = parseInt($("#eTime").val().split(":")[0] * 60) + parseInt($("#eTime").val().split(":")[1]);
        if (sTime && eTime || sTime == 0) {
            $('#timeRange').slider('values', 0, sTime).slider('values', 1, eTime);
        }
        $('#sTimeBubble').text($("#sTime").val()).css({'left':$('#timeRange .ui-slider-handle:first').offset().left});
        $('#eTimeBubble').text($("#eTime").val()).css({'left':$('#timeRange .ui-slider-handle:last').offset().left});
    }

    IndicoUI.executeOnLoad(function()
    {
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
                $("#sDay").val($("#sDatePlace").datepicker('getDate').getDate());
                $("#sMonth").val(parseInt($("#sDatePlace").datepicker('getDate').getMonth() + 1));
                $("#sYear").val($("#sDatePlace").datepicker('getDate').getFullYear());
                $("#eDay").val($("#eDatePlace").datepicker('getDate').getDate());
                $("#eMonth").val(parseInt($("#eDatePlace").datepicker('getDate').getMonth() + 1));
                $("#eYear").val($("#eDatePlace").datepicker('getDate').getFullYear());
                forms_are_valid();
                set_repeatition_comment();
            }
        });

        $("#sDatePlace").datepicker('setDate', new Date ($("#sYear").val() + "/" + $("#sMonth").val() + "/" + $("#sDay").val()));
        $("#eDatePlace").datepicker('setDate', new Date ($("#eYear").val() + "/" + $("#eMonth").val() + "/" + $("#eDay").val()));

        $('#sTime').watermark('hh:mm');
        $('#eTime').watermark('hh:mm');

        $("#sTime").val('${ startT }');
        $("#eTime").val('${ endT }');

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
                forms_are_valid();
                updateTimeSlider(event,ui);

            },
          });

       % if startDT.day != '':
            $("#sDatePlace").datepicker('setDate', new Date (${ startDT.year } + "/" + ${ startDT.month } + "/" + ${ startDT.day }));
        % endif

        % if endDT.day != '':
            $("#eDatePlace").datepicker('setDate', new Date (${ endDT.year } + "/" + ${ endDT.month } + "/" + ${ endDT.day }));
        % endif


     });
</script>
% if unavailableDates:
<tr id="sdatesTR" >
    <td class="subFieldWidth" align="right" valign="top" ><small>${ _("Unavailability") }</small></td>
    <td class="blacktext">
    <span style="color:#881122">${ _("This room cannot be booked during the following dates due to maintenance reasons") }:<ul><li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartDate().strftime('%d/%m/%Y'), x.getEndDate().strftime('%d/%m/%Y')), unavailableDates )) }</li></ul></span>
    </td>
</tr>
% endif
% if maxAdvanceDays:
<tr id="sdatesTR" >
    <td class="subFieldWidth" align="right" valign="top" ><small>${ _("Time range restriction") }</small></td>
    <td class="blacktext">
    <span style="color:#881122">${ _("This room cannot be booked more than %s days in advance") % maxAdvanceDays }</span>
    </td>
</tr>
% endif

<tr id="sdatesTR" style="text-align: center;" >
    <td>
        <div id="sDatePlaceDiv" class="label titleCellFormat" style="clear: both; float: left; padding-right: 14px;">
            ${ _("Booking date")}
            <div id="sDatePlace"></div>
        </div>
        <div id="sDatePlaceDiv" class="label titleCellFormat" style="float: left;">
            ${ _("End date")}
            <div id="eDatePlace"></div>
        </div>
        <div class="infoMessage" id="holidays-warning" style="float: left; display: none"></div>
        <input type="hidden" name="sdate" id="sdate"/>
        <input type="hidden" name="edate" id="edate"/>
        <input type="hidden" value="${ startDT.day }" name="sDay" id="sDay"/>
        <input type="hidden" value="${ startDT.month }" name="sMonth" id="sMonth"/>
        <input type="hidden" value="${ startDT.year }" name="sYear" id="sYear"/>
        <input type="hidden" value="${ endDT.day }" name="eDay" id="eDay"/>
        <input type="hidden" value="${ endDT.month }" name="eMonth" id="eMonth"/>
        <input type="hidden" value="${ endDT.year }" name="eYear" id="eYear"/>
    </td>
</tr>
<tr id="hoursTR">
    <td>
        <small> ${ _("Booking time from")}&nbsp;&nbsp;</small>
        <input name="sTime" id="sTime" style="width: 43px;" type="text" />
        <small> ${ _("to")}&nbsp;</small>
        <input name="eTime" id="eTime" style="width: 43px;" type="text" />
        <div style="margin: 20px 0px 54px 0px">
            <div id="minHour" style="float: left; color: gray; padding-right: 12px">0:00</div>
            <div id="timeRange" style="width: 370px; float: left;"></div>
            <div id="maxHour" style="float: left; color: gray; padding-left: 12px">23:59</div>
            <div id="sTimeBubble" style="position: absolute; margin: -19px 0px 0px -8px;">&nbsp;</div>
            <div id="eTimeBubble" style="position: absolute; margin: 20px 0px 0px -8px;">&nbsp;</div>
        </div>
    </td>
</tr>
<tr id="repTypeTR">
    <td>
        <small> ${ _("Type")}&nbsp;&nbsp;</small>
        <select name="repeatability" id="repeatability" onchange="set_repeatition_comment();">
        <% sel = [ "", "", "", "", "", "" ]; %>
        % if repeatability == None:
        <%     sel[5] = 'selected="selected"' %>
        % endif
        % if repeatability != None:
        <%     sel[repeatability] = 'selected="selected"' %>
        % endif
            <option ${ sel[5] } value="None"> ${ _("Single reservation")}</option>
            <option ${ sel[0] } value="0"> ${ _("Repeat daily")}</option>
            <option ${ sel[1] } value="1"> ${ _("Repeat once a week")}</option>
            <option ${ sel[2] } value="2"> ${ _("Repeat once every two weeks")}</option>
            <option ${ sel[3] } value="3"> ${ _("Repeat once every three weeks")}</option>
            <option ${ sel[4] } value="4"> ${ _("Repeat every month")}</option>
        </select>
        <span id="repComment" style="margin-left: 12px"></span>
        ${contextHelp('repeatitionHelp' )}
</tr>
