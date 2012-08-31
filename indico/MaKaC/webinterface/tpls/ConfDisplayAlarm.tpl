<%from indico.util.date_time import format_datetime, format_date, format_time%>

<%def name="printRecipientList(alarm)">
    <% addr = "" %>
    % for user in alarm.getToUserList():
          <% addr = addr + user.getEmail() + " <br> " %>
    % endfor
    % if alarm.getToAllParticipants() :
          <% addr = "to all participants" + "<br>" %>
    % endif
    % if len(alarm.getToAddrList()) > 0 :
          <% addr = addr + " <br> ".join(alarm.getToAddrList()) + "<br> " %>
    % endif
    ${addr}
</%def>

<%def name="printStartDate(alarm)">
    ${format_datetime(alarm.getStartOn(),format='d MMM yyyy HH:mm', timezone=confTZ)}
    % if alarm.getTimeBefore() is not None:
          <%
          tb = alarm.getTimeBefore()
          d = tb.days
          %>
          % if d != 0:
                ${"(Day -%s)" %d}
          % else:
                ${"(Hour -%s )" % (tb.seconds/3600)}
          % endif
    % endif
</%def>

<table width="100%" border="0">
    <tr>
        <td colspan="4" nowrap class="groupTitle">
             ${ _("List of existing alarms")}
        </td>
    </tr>
    <tr>
        <td bgcolor="white" width="90%">
            <table width="80%">
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
                        % if al.getEndedOn():
                            <span class="alarmSent">
                                ${al.getSubject()}
                                ${ ("(" +_("Sent the ") + al.getStartedOn().astimezone(confTZ).strftime(dtFormat) +")")}
                            </span>
                        % elif al.getId() :
                            <a href="${modifyAlarmURL}?${al.getLocator().getURLForm()}" >${al.getSubject()}</a>
                        % else:
                            <span class="notScheduled">
                                ${al.getSubject()}
                            </span>
                        % endif
                        </td>
                        <td nowrap>${printRecipientList(al)}</td>
                        <td align="center">
                        % if al.getEndedOn():
                            <span class="alarmSentDelete">${_("Delete")}</span>
                        % elif al.getId():
                            <a href="${deleteAlarmURL}?${al.getLocator().getURLForm()}" class="deleteAlarm">${_("Delete")}</a>
                        % else:
                            <span class="notScheduled">${_("Delete")}</span>
                        % endif:
                        </td>
                    </tr>
                % endfor
            % endif
            </table>
        </td>
    </tr>
</table>

<table width="100%">
  <form action="${ addAlarmURL }" method="POST">
  <tr>
    <td>
      <input type="submit" class="btn" value="${ _("add new alarm")}">
    </td>
  </tr>
  </form>
</table>

<script type="text/javascript">
IndicoUI.executeOnLoad(function(){
    $('span.alarmSent').qtip({content: '${_("The alarm has already been sent.")}', position: {my: 'top middle', at: 'bottom middle'}});
    $('span.alarmSentDelete').qtip({content: '${_("Sent alarms cannot be deleted.")}', position: {my: 'top middle', at: 'bottom middle'}});
    $('span.notScheduled').qtip({content: '${_("The alarm is being scheduled, please wait some seconds and refresh the page.")}', position: {my: 'top middle', at: 'bottom middle'}});
    $(".deleteAlarm").click(function(cosa){
        var self = this;
        new ConfirmPopup($T("Delete alarm"), $T("Are you sure to delete this alarm?"), function(confirmed){
            if(confirmed){
                window.location = self.getAttribute("href");
            }
        }).open();
        return false;
    });
});
</script>
