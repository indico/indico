<form action=${ postURL } method="post">
<table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td class="groupTitle" colspan="2">${ _("Editing schedule basic data")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Start date")}</span></td>
        <td bgcolor="white" width="100%">
            <table>
                <tr>
                <td>
                <span id="sDatePlace"></span>
                <input type="hidden" value="${ sDay }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ sMonth }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ sYear }" name="sYear" id="sYear"/>
                <input type="hidden" value="${ sHour }" name="sHour" id="sHour" />
                <input type="hidden" value="${ sMin }" name="sMin" id="sMin" />
                </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("End date")}</span></td>
        <td bgcolor="white" width="100%">
            <table>
                <tr>
                    <td>
                        <span id="eDatePlace"></span>
                <input type="hidden" value="${ eDay }" name="eDay" id="eDay"/>
                <input type="hidden" value="${ eMonth }" name="eMonth" id="eMonth"/>
                <input type="hidden" value="${ eYear }" name="eYear" id="eYear"/>
                <input type="hidden" value="${ eHour }" name="eHour" id="eHour" />
                <input type="hidden" value="${ eMin }" name="eMin" id="eMin" />
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td align="left" colspan="2"><input type="submit" class="btn" value="${ _("submit")}" name="OK"> <input type="submit" class="btn" value="${ _("cancel")}" name="CANCEL"></td>
    </tr>
</table>
</form>
<script  type="text/javascript">

        IndicoUI.executeOnLoad(function()
    {

        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMin']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMin']);
        $E('eDatePlace').set(endDate);

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear } ${"0"+ sHour  if len (sHour) == 1 else  sHour }:${"0"+ sMin  if len (sMin) == 1 else  sMin }');
        % endif

        % if eDay != '':
            endDate.set('${ eDay }/${ eMonth }/${ eYear } ${"0"+ eHour  if len (eHour) == 1 else  eHour }:${"0"+ eMin  if len (eMin) == 1 else  eMin }');
        % endif
    });
</script>
