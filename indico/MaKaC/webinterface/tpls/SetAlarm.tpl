<table width="60%" border="0">
  <tr>
    <td colspan="5" class="groupTitle">${ formTitle }</td>
  </tr>
  <tr>
    <td>
<br>
<TABLE border="0" align="center" width="100%">
<form method="POST" name="alarmForm" id="alarmForm">
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
        <input name="dateType" id="dateType" type="radio" value="1" ${ "checked" if dateType == 1 else "" }>  ${ _("At this date")}:
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
        <input name="dateType" id="dateType" type="radio" value="2" ${ "checked" if dateType == 2 else "" }> ${ _("Time before the beginning of the event")}:
    </td>
    <td>
        <input size="3" name="timeBefore" id="timeBefore" value="${timeBefore}">

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
        <td>&nbsp;<input type="checkbox" name="toAllParticipants" id="toAllParticipants" ${"checked" if toAllParticipants else ""}></td>
        <% toPartOrReg =  _("participants") if conference.getType() != "conference" else _("registrants") %>
        <td> ${_("Send alarm to all %s of the event.")%toPartOrReg }</td>
    </tr>
    <tr>
        <td>&nbsp;<input type="checkbox" name="defineRecipients" id="defineRecipients" ${ "checked" if Emails!="" else "" }></td>
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
            <input type="submit" class="btn" value="${ _("Save")}" id="save">
            <input type="submit" class="btn" value="${_("Send now")}" id="sendNow" >
            <input type="submit" class="btn" value="${_("Send me as a test")}" id="sendTest">
             <input type="submit" class="btn" value="${ _("Cancel")}" id="cancel">

        </td>
    </tr>
</form>
</table>
<br>
</td></tr>

</table>

<script type="text/javascript">
var sendTestAlarm = function ()
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
    $("#defineRecipients").click(function ()
    {
        if ($("#email").is(":disabled")){
            $("#email").removeAttr("disabled");
        } else {
            $("#email").attr("disabled",true);
        }
    });
    var dateAlarm = IndicoUI.Widgets.Generic.dateField(true,null,['day', 'month', 'year','hour', 'minute']);
    $('#datePlace').append($(dateAlarm.dom));
    % if day != '':
        dateAlarm.set('${ day }/${ month }/${ year } ${ hour }:${ minute }');
    % endif
    var checkRecipients = function(){
        if(!$('#toAllParticipants').attr('checked') && (!$('#defineRecipients').attr('checked')||($('#defineRecipients').attr('checked') && $("#email").val()=="")) ){
            return Html.span({}, $T("Please select the checkbox 'Send to all participants' or 'Define recipients' with a list of emails."));
        }
        return null;
    };
    var parameterManagerTest = new IndicoUtil.parameterManager();
    parameterManagerTest.add($E('fromAddr'),'select',false,null);
    var parameterManager = new IndicoUtil.parameterManager();
    parameterManager.add($E('fromAddr'),'select',false,null);
    parameterManager.add($E('toAllParticipants'),'checkbox',true,checkRecipients);
    parameterManager.add($E('defineRecipients'),'checkbox',true,checkRecipients);
    parameterManager.add($E('email'),'text',true,checkRecipients);
    parameterManager.add($E('timeBefore'),'int',true,function(){
        if($('[name=dateType]:checked').val() == "2" && (!IndicoUtil.isInteger($('#timeBefore').attr("value")) || $('#timeBefore').attr("value")<=0)){
            return Html.span({}, $T("The time before must be a positive number"));
        }
        return null;
    });
    parameterManager.add($E('dateType'),'radio',false,null);
    $('#Save').click(function(){
        if (!parameterManager.check()) {
            alert($T('The form contains some errors. Please, correct them and submit again.'));
            return false;
        }
        return true;
    });
    $('#save').click(function(){
        this.form.action = '${ urlHandlers.UHSaveAlarm.getURL( conference ) }';
        return parameterManager.check();
    });

    $('#sendNow').click(function(){
        this.form.action = '${urlHandlers.UHSendAlarmNow.getURL( conference )}';
        return parameterManager.check();
    });
    $('#sendTest').click(function(){
        if(parameterManagerTest.check()){
            sendTestAlarm();
        }
        return false;
    });
    $('#cancel').click(function(){
        this.form.action = '${urlHandlers.UHConfDisplayAlarm.getURL( conference )}';
    });
});
</script>