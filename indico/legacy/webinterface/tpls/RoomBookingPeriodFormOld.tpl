<%page args=""/>
<script type="text/javascript">

    IndicoUI.executeOnLoad(function()
    {
        var startDate = IndicoUI.Widgets.Generic.dateField_sdate(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField_edate(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);

        /* In case the date changes, we need to check whether the start date is greater than the end date,
        and if it's so we need to change it */
        startDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                endDate.set(startDate.get());
                set_repeatition_comment();
            }
            updateFields();
        });

        endDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                startDate.set(endDate.get());
                set_repeatition_comment();
            }
            updateFields();
        });

        $('#sTime, #eTime').on('change', function() {
            updateFields();
        });

        function updateFields() {
            $('#start_dt').val('{0}/{1}/{2} {3}'.format($('#sDay').val(), $('#sMonth').val(), $('#sYear').val(), $('#sTime').val()));
            $('#end_dt').val('{0}/{1}/{2} {3}'.format($('#eDay').val(), $('#eMonth').val(), $('#eYear').val(), $('#eTime').val()));
        }

        % if startDT.day != '':
            startDate.set('${ startDT.day }/${ startDT.month }/${ startDT.year }');
        % endif

        % if endDT.day != '':
            endDate.set('${ endDT.day }/${ endDT.month }/${ endDT.year }');
        % endif

        updateFields();
     });
</script>
    <tr id="sdatesTR" >
        <td class="subFieldWidth" align="right" > ${ _("Start Date")}&nbsp;&nbsp;</td>
        <td class="blacktext">
            <span id="sDatePlace"></span>
            <input type="hidden" value="${ startDT.day }" name="sDay" id="sDay"/>
            <input type="hidden" value="${ startDT.month }" name="sMonth" id="sMonth"/>
            <input type="hidden" value="${ startDT.year }" name="sYear" id="sYear"/>
        </td>
      </tr>
     <tr id="edatesTR" >
        <td class="subFieldWidth" align="right" >${ _("End Date")}&nbsp;&nbsp;</td>
        <td>
            <span id="eDatePlace"></span>
            <input type="hidden" value="${ endDT.day }" name="eDay" id="eDay"/>
            <input type="hidden" value="${ endDT.month }" name="eMonth" id="eMonth"/>
            <input type="hidden" value="${ endDT.year }" name="eYear" id="eYear"/>
        </td>
    </tr>
    <tr id="hoursTR" >
        <td class="subFieldWidth" align="right" >${ _("Hours")}&nbsp;&nbsp;</td>
        <td align="left" class="blacktext">
            <input name="sTime" id="sTime" maxlength="5" size="5" type="text" value="${ startT }"> &nbsp;&mdash;&nbsp;
            <input name="eTime" id="eTime" maxlength="5" size="5" type="text" value="${ endT }">
            <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
        </td>
    </tr>
    <tr id="repTypeTR" >
        <td class="subFieldWidth" align="right" >${ _("Type")}&nbsp;&nbsp;</td>
        <td align="left" class="blacktext" >
            <select name="repeatability" id="repeatability" onchange="set_repeatition_comment();">
                <option value="None" selected> ${ _("Single day")}</option>
                <option value="0"> ${ _("Repeat daily")}</option>
                <option value="1"> ${ _("Repeat once a week")}</option>
                <option value="2"> ${ _("Repeat once every two weeks")}</option>
                <option value="3"> ${ _("Repeat once every three weeks")}</option>
                <option value="4"> ${ _("Repeat every month")}</option>
            </select>
            <span id="repComment" style="margin-left: 12px"></span>
            ${contextHelp('repetitionHelp' )}
        </td>
    </tr>
