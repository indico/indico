<%page args=""/>
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
