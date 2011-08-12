<%def name="printRecipientList(alarm)">
    <% addr = "" %>
    % if len(alarm.getToAddrList()) > 0 :
          <% addr = " <br> ".join(alarm.getToAddrList()) + " <br> " %>
    % endif
    % for user in alarm.getToUserList():
          <% addr = addr + user.getEmail() + " <br> " %>
    % endfor
    % if alarm.getToAllParticipants() :
          <% addr = "to all participants" %>
    % endif
    ${addr}
</%def>

<%def name="printStartDate(alarm)">
    <% dateStart = alarm.getStartOn().astimezone(confTZ) %>
    % if alarm.getTimeBefore() is not None:
          <%
          tb = alarm.getTimeBefore()
          d = tb.days
          %>
          % if d < 0:
                ${dateStart.strftime(dtFormat)}
          % elif d != 0:
                ${"D-%s (%s)" % (d,dateStart.strftime(dtFormat))}
          % else:
                ${"H-%s (%s)" % (tb.seconds/3600,dateStart.strftime(dtFormat))}
          % endif
    % elif dateStart is not None:
          ${dateStart.strftime(dtFormat)}
    % else:
          ${_("not set")}
    % endif
</%def>

<table align="center" width="90%">
  <form action="${ addAlarmURL }" method="POST">
  <tr>
    <td>
      <input type="submit" class="btn" value="${ _("add new alarm")}">
    </td>
  </tr>
  </form>
</table>

<table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="4" nowrap class="groupTitle">
             ${ _("List of existing alarms")}
        </td>
    </tr>
    <tr>
        <td bgcolor="white" width="90%">
            <table width="100%">
                <tr>
                    <td nowrap class="titleCellFormat">${ _("Date")} (${ timezone }):</td>
                    <td nowrap class="titleCellFormat">${ _("Subject")}:</b></td>
                    <td nowrap class="titleCellFormat">${ _("To")}:</b></td>
                    <td nowrap class="titleCellFormat">${ _("Action")}:</td>
                </tr>
            % if not alarmList:
                <tr><td colspan="4"><em>${ _("There are not alarms yet")}</em></td></tr>
            % else:
                % for al in alarmList:
                    <tr>
                        <td nowrap>
                        ${printStartDate(al)}
                        </td>
                        <td width="60%">
                        % if al.getId():
                            % if al.getEndedOn():
                                   <span class="alarmSent">
                                       ${al.getSubject()}
                                       ${ ("(" +_("Sent the ") + al.getStartedOn().astimezone(confTZ).strftime(dtFormat) +")")}
                                   </span>
                            % else:
                                 <a href="${modifyAlarmURL}?${al.getLocator().getURLForm()}" >${al.getSubject()}</a>
                            % endif
                        % else:
                            <span class="notScheduled">
                                ${al.getSubject()}
                            </span>
                        % endif
                        </td>
                        <td nowrap>${printRecipientList(al)}</td>
                        <td align="center">
                        % if al.getId():
                             <a href="${deleteAlarmURL}?${al.getLocator().getURLForm()}" onclick="return confirm('${_("Are you sure to delete this alarm?")}');">${_("Delete")}</a>
                        % else:
                             <span class="notScheduled">
                                 ${_("Delete")}
                             </span>
                        % endif:
                        </td>
                    </tr>
                % endfor
            % endif
            </table>
        </td>
    </tr>
</table>
<script type="text/javascript">
IndicoUI.executeOnLoad(function(){
    $('span.alarmSent').qtip({content: '${alarmSentMsg}', position: {my: 'top middle', at: 'bottom middle'}});
    $('span.notScheduled').qtip({content: '${notScheduledMsg}', position: {my: 'top middle', at: 'bottom middle'}});
});
</script>
