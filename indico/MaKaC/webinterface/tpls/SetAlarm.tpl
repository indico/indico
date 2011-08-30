<table width="60%" border="0">
  <tr>
    <td colspan="5" class="groupTitle">${ formTitle }</td>
  </tr>
  <tr>
    <td>
<br>
<TABLE border="0" align="center" width="100%">
<form method="POST" name="alarmForm">
<input type="hidden" name="alarmId" value="${ alarmId }">
    <tr>
      <td align="right">
      </td>
      <TD>
<table>
<tr>
    <td align="left" colspan="2">
        <b>&nbsp; ${ _("When to send the alarm?")}&nbsp;</b>
    </td>
</tr>
<tr>
    <td>
        <input name="dateType" type="radio" value="1" ${ "checked" if dateType == 1 else "" }>  ${ _("At this date")}:
    </td>
    <td nowrap class="contentCellTD">
                <span id="datePlace"></span>
                <input type="hidden" id="day" name="day" value="${ day }">
                <input type="hidden" id="month"  name="month" value="${ month }">
                <input type="hidden" id="year" name="year" value="${ year }">
                <input type="hidden" id="hour" name="hour" value="${ hour }">
                <input type="hidden" id="minute" name="minute" value="${ minute }">
        (${ timezone })
    </td>
</tr>
<tr>
   <td>
        <input name="dateType" type="radio" value="2" ${ "checked" if dateType == 2 else "" }> ${ _("Time before the beginning of the event")}:
    </td>
    <td>
        <input size="3" name="timeBefore" value="${timeBefore}">

        <select name=timeTypeBefore >
                <option value="hours" ${"selected" if dateType == 2 else ""}>${_("Hours")}
                <option value="days" ${"selected" if dateType == 3 else ""}>${_("Days")}
        </select>
  </td>
</tr>
</table>
</td>
</tr>
<tr><td colspan="2" align="center">

<br>
<table width="100%">
    <tr>
        <td colspan="2"><b>&nbsp; ${ _("From address")}:</b></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td>
            <select name="fromAddr" id="fromAddr" style="width:425px">
                <option value="">--${_("select a from address")}--</option>
                % for contact in fromList:
                    <option value="${contact}" ${"selected" if fromAddr.strip() == contact else ""}>
                    % if contact == fromList[contact]:
                        ${contact}
                    % else:
                        ${fromList[contact]} &#60;${contact}&#62;
                    % endif
                    </option>
                % endfor
            </select>
        </td>
    </tr>
       <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2"><b>&nbsp; ${ _("Send alarm to")}:</b></td>
    </tr>
    <tr>
        <td>&nbsp;<input type="checkbox" name="toAllParticipants" ${"checked" if toAllParticipants else ""}></td>
        <% toPartOrReg =  _("participants") if conference.getType() != "conference" else _("registrants") %>
        <td> ${_("Send alarm to all %s of the event.")%toPartOrReg }</td>
    </tr>
    <tr>
        <td>&nbsp;<input type="checkbox" name="defineRecipients" onClick="setEmailsState()" ${ "checked" if Emails!="" else "" }></td>
        <td> ${ _("Define recipients (comma-separated list of email addresses)")} :</td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td><input type="text" name="Emails" id="email" size="90%" ${ "disabled='disabled'" if Emails=="" else "" }value="${ Emails }"></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="2"><b>&nbsp; ${ _("Additional Note")}:</b></td>
    <tr>
    </tr>
        <td>&nbsp;</td>
        <td align="right"><textarea id="note" name="note" rows="5" style="width:100%;" >${ note }</textarea></td>
    </tr>
    <tr>
        <td colspan="2" align="left">
        <br>
        &nbsp;<input name="includeConf" id="includeConf" type="checkbox" value="1" ${ "checked" if includeConf else ""}> ${ _("Include a text version of the agenda in the email")}
        </td>
    </tr>
</table>
      </TD></tr>
    <tr>
        <td align="center" colspan="2">
            <br>
            <input type="submit" class="btn" value="${ _("Save")}" onClick="this.form.action='${ urlHandlers.UHSaveAlarm.getURL( conference ) }'">
            <input type="submit" class="btn" value="${_("Send now")}" onClick="this.form.action='${urlHandlers.UHSendAlarmNow.getURL(conference)}';">
            <input type="submit" class="btn" value="${_("Send me as a test")}" onClick="return sendTestAlarm(this.form); return false;">
             <input type="submit" class="btn" value="${ _("Cancel")}" onClick="this.form.action='${urlHandlers.UHConfDisplayAlarm.getURL( conference )}';">
        </td>
    </tr>
</form>
</table>
<br>
</td></tr>

</table>

<script type="text/javascript">
var setEmailsState = function ()
{
    if ($("#email").is(":disabled")){
        $("#email").removeAttr("disabled");
    } else {
        $("#email").attr("disabled",true);
    }
};

var sendTestAlarm = function (form)
{
    var killProgress = IndicoUI.Dialogs.Util.progress($T("Sending the test alarm..."));
    indicoRequest('event.alarm.sendTestNow', {
        confId: ${conference.getId()},
        fromAddr: $("#fromAddr").val(),
        note: $("#note").val(),
        includeConf: $("#includeConf:checked").val(),
    },
    function(result, error) {
        if(error) {
            IndicoUtil.errorReport(error);
            killProgress();
        } else{
            killProgress();
            (new AlertPopup($T('Email sent'),$T("The test alarm has been sent succesfully."))).open();
        }
    });
    return false;
};

IndicoUI.executeOnLoad(function()
{
    var dateAlarm = IndicoUI.Widgets.Generic.dateField(true,null,['day', 'month', 'year','hour', 'minute']);
    $('#datePlace').append($(dateAlarm.dom));
    % if day != '':
        dateAlarm.set('${ day }/${ month }/${ year } ${ hour }:${ minute }');
    % endif
});
</script>