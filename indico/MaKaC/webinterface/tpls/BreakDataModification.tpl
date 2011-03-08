<form id="BreakDataModificationForm" method="POST" action=${ postURL }>
<table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px;">
        <tr>
            <td class="groupTitle" colspan="2">${ WPtitle }</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Title")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <input type="text" name="title" size="60" value=${ title }>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Description")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <textarea name="description" cols="60" rows="6">${ description }</textarea>
            </td>
        </tr>
    <tr>


        <%include file="EventLocationInfo.tpl" args="event=self_._rh._break, modifying=True, parentRoomInfo=roomInfo(self_._rh._break, level='inherited'), showParent=True, conf = False"/>

    </tr>
    <tr>
            <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Start date")}</span></td>
            <td bgcolor="white" width="100%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="${ sDay }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ sMonth }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ sYear }" name="sYear" id="sYear"/>
                <input type="hidden" value="${ sHour }" name="sHour" id="sHour" />
                <input type="hidden" value="${ sMinute }" name="sMinute" id="sMinute" />
        ${ autoUpdate }
                ${ schOptions }
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> ${ _("Duration")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <input type="text" size="2" name="durHours"
                    value=${ durationHours }>:
                <input type="text" size="2" name="durMins"
                    value=${ durationMinutes }>
            </td>
        </tr>
${ Colors }
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
        <input type="submit" class="btn" name="OK" value="${ _("ok")}">
        <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
IndicoUI.executeOnLoad(function()
    {
        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear } ${"0"+ sHour  if len (sHour) == 1 else  sHour }:${"0"+ sMinute  if len (sMinute) == 1 else  sMinute }');
        % endif
    });
injectValuesInForm($E('BreakDataModificationForm'));

</script>