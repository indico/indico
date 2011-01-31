<form method="GET" action="<%= postURL %>" id="ContributionCreationForm">
<%= locator %>
<table width="60%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
<tr>
  <td colspan="2">
    <input type="hidden" name="orginURL" value="<%= orginURL %>">
    <input type="hidden" name="sessionId" value="<%= sessionId %>">
    <input type="hidden" name="slotId" value="<%= slotId %>">
    <input type="hidden" name="eventType" value="<%= eventType %>">
    <input type="hidden" name="contributionCreatedFrom" value="<%= contributionCreatedFrom %>">
    <%= errorMsg %>
    <%= infoMsg %>
  </td>
</tr>
<tr>
  <td colspan="2" class="groupTitle"><%= _("Create new contribution")%></td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Title")%></span></td>
  <td bgcolor="white" width="100%">
    <input type="text" name="title" size="80" value=<%= title %>>
  </td>
</tr>
<%
if self._rh._target.getConference().hasEnabledSection("cfa") and self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
%>
<%= additionalFields %>
<%end%>
<%
    else:
%>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Description")%></span></td>
  <td bgcolor="white" width="100%">
    <textarea name="description" cols="80" rows="10" wrap="soft"><%= description %></textarea>
  </td>
</tr>
<%end%>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Keywords")%></span></td>
  <td bgcolor="white" width="100%">
    <textarea name="keywords" cols="60" rows="3"><%= keywords %></textarea>
  </td>
</tr>
		<%= typeModule %>

		<% includeTpl('EventLocationInfo', parentRoomInfo=roomInfo(self._rh._target), modifying=False, showParent=True), conf = False %>


		<%= boardModule %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Start Date")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="sDay" value="<%= day %>" onChange="">-
                <input type="text" size="2" name="sMonth" value="<%= month %>" onChange="">-
                <input type="text" size="4" name="sYear" value="<%= year %>" onChange="">
                <input type="image" src=<%= calendarIconURL %> alt="open calendar" border="0" onClick="javascript:window.open('<%= calendarSelectURL %>?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <input type="text" size="2" name="sHour" value="<%= sHour %>">:
                <input type="text" size="2" name="sMinute" value="<%= sMinute %>">
		<%= autoUpdate %>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Duration")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="durHours" value="<%= durationHours %>">:
                <input type="text" size="2" name="durMins" value="<%= durationMinutes %>">
            </td>
        </tr>
<%= presenterFreeText %>
<%= author %>
<%= coauthor %>
<%= presenter %>
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
		<input type="submit" class="btn" value="<%= _("ok")%>" name="ok">
		<input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">

injectValuesInForm($E('ContributionCreationForm'));

</script>