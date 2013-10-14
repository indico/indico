<%page args="repeatability=None, form=None, unavailableDates=None, availableDayPeriods=None, maxAdvanceDays=None"/>
<script type="text/javascript">

    IndicoUI.executeOnLoad(function()
    {
        % if not infoBookingMode:
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

            $('#repeatability').change(function() {
                if ($(this).val() != 'None') {
                    $('#sDatePlaceTitle').text('${ _("Start date")}');
                    $('#finishDate').val('true');
                    $('#eDatePlaceDiv').show();
                }
                else {
                    $('#sDatePlaceTitle').text('${ _("Booking date")}');
                    $('#finishDate').val('false');
                    $('#eDatePlaceDiv').hide();
                }
                refreshDates();
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
                    refreshDates();
                    forms_are_valid();
                    set_repeatition_comment();
                }
            });

            % if startDT.day != '':
                $("#sDatePlace").datepicker('setDate', new Date (${ startDT.year } + "/" + ${ startDT.month } + "/" + ${ startDT.day }));
            % endif

            % if endDT.day != '':
                $("#eDatePlace").datepicker('setDate', new Date (${ endDT.year } + "/" + ${ endDT.month } + "/" + ${ endDT.day }));
            % endif

            $('#sTime').watermark('hh:mm');
            $('#eTime').watermark('hh:mm');

            $("#sTime").val('${ startT }');
            $("#eTime").val('${ endT }');

            updateTimeSlider();
            $('#repeatability').change();
        % else:

            $('#typeInfo').text($('#repeatability option:selected').text());
        % endif


     });
</script>
% if unavailableDates:
<tr>
    <td colspan="2">
        <div class="infoMessage" style="float: left;">
            <strong>${ _("Unavailability") }: </strong>
            ${ _("This room cannot be booked during the following dates due to maintenance reasons") }:
            <ul style="text-align: left">
                <li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartDate().strftime('%d/%m/%Y'), x.getEndDate().strftime('%d/%m/%Y')), unavailableDates )) }</li>
            </ul>
        </div>
    </td>
</tr>
% endif
% if availableDayPeriods:
<tr>
    <td colspan="2">
        <div class="infoMessage" style="float: left;">
            <strong>${ _("Available day periods") }: </strong>
            ${ _("This room can only be booked during the following time periods") }:
            <ul style="text-align: left">
                <li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartTime(), x.getEndTime()), availableDayPeriods )) }</li>
            </ul>
        </div>
    </td>
</tr>
% endif
% if maxAdvanceDays:
<tr>
    <td colspan="2">
        <div class="infoMessage" style="float: left;">
            <strong>${ _("Time range restriction") }: </strong>
            ${ _("This room cannot be booked more than %s days in advance") % maxAdvanceDays }
        </div>
    </td>
</tr>
% endif

<tr>
    <td colspan="2">
        % if infoBookingMode:
            <div style="display: none">
        % else:
            <div style="float: left; clear: both; padding-bottom: 20px;">
        % endif
        ${ _("Type")}&nbsp;&nbsp;
        <select name="repeatability" id="repeatability" style=" width: 230px;" onchange="set_repeatition_comment();">
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
        <span id="repComment"></span>
        ${contextHelp('repeatitionHelp' )}
        </div>
     </td>
</tr>
% if not infoBookingMode:
<tr style="text-align: center;" >
    <td colspan="2">
        <div id="sDatePlaceDiv" class="titleCellFormat bookDateDiv" style="clear: both;">
            <div id='sDatePlaceTitle' class='label'>${ _("Booking date")}</div>
            <div id="sDatePlace"></div>
        </div>
        <div id="eDatePlaceDiv" class="titleCellFormat bookDateDiv">
            <div id='eDatePlaceTitle' class='label'>${ _("End date")}</div>
            <div id="eDatePlace"></div>
        </div>
        <div class="infoMessage" id="holidays-warning" style="float: left; display: none"></div>
    </td>
</tr>
<tr>
    <td colspan="2">
        <div style="float: left; clear: both; padding: 20px 32px; background-color: #FAFAFA; margin-top: 10px;">
        ${ _("Booking time from")}&nbsp;&nbsp;
        <input name="sTime" id="sTime" style="width: 43px;" type="text" />
        ${ _("to")}&nbsp;
        <input name="eTime" id="eTime" style="width: 43px;" type="text" />
        <div style="margin: 25px 0px 54px 0px">
            <div id="minHour" style="float: left; color: gray; padding-right: 12px">0:00</div>
            <div id="timeRange" style="width: 370px; float: left;"></div>
            <div id="maxHour" style="float: left; color: gray; padding-left: 12px">23:59</div>
            <div id="sTimeBubble" style="position: absolute; margin: -19px 0px 0px -8px;">&nbsp;</div>
            <div id="eTimeBubble" style="position: absolute; margin: 20px 0px 0px -8px;">&nbsp;</div>
        </div>
        </div>
    </td>
</tr>
<tr>
    <td>&nbsp;</td>
</tr>
<tr>
    <td colspan="2">
        <a name="conflicts"></a>
        <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
          <li class="button" onclick="checkBooking()">
            <a href="#" onClick="return false;">${ _("Check for conflicts")}</a>
          </li>
          <li style="display: none"></li>
        </ul>
    <td>
</tr>
% else:
<tr>
    <td class="subFieldWidth" align="right" valign="top">${ _("Type")}&nbsp;&nbsp;</td>
    <td align="left" class="blacktext" id="typeInfo"></td>
</tr>
<tr>
    <td class="subFieldWidth" align="right" valign="top">${ _("Start date")}&nbsp;&nbsp;</td>
    <td align="left" class="blacktext">${ startDT.day }/${ startDT.month }/${ startDT.year }</td>
</tr>
<tr>
    <td class="subFieldWidth" align="right" valign="top">${ _("End date")}&nbsp;&nbsp;</td>
    <td align="left" class="blacktext">${ endDT.day }/${ endDT.month }/${ endDT.year }</td>
</tr>
<tr>
    <td class="subFieldWidth" align="right" valign="top">${ _("Hours")}&nbsp;&nbsp;</td>
    <td align="left" class="blacktext">${ startT } - ${ endT }</td>
</tr>
% endif

