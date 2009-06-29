<form method="GET" action="%(postURL)s" id="ContributionCreationForm">
%(locator)s
<table width="60%%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">    	
<tr>
  <td colspan="2">
    <input type="hidden" name="orginURL" value="%(orginURL)s">
    <input type="hidden" name="sessionId" value="%(sessionId)s">
    <input type="hidden" name="slotId" value="%(slotId)s">
    <input type="hidden" name="eventType" value="%(eventType)s">
    <input type="hidden" name="contributionCreatedFrom" value="%(contributionCreatedFrom)s">
    %(errorMsg)s
    %(infoMsg)s
  </td>
</tr>
<tr>
  <td colspan="2" class="groupTitle"><%= _("Create new contribution")%></td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Title")%></span></td>
  <td bgcolor="white" width="100%%">
    <input type="text" name="title" size="80" value=%(title)s>
  </td>
</tr>
<%
if self._rh._target.getConference().hasEnabledSection("cfa") and self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
%>
%(additionalFields)s
<%end%>
<%
    else:
%>     
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Description")%></span></td>
  <td bgcolor="white" width="100%%">
    <textarea name="description" cols="80" rows="10" wrap="soft">%(description)s</textarea>
  </td>
</tr>
<%end%>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Keywords")%></span></td>
  <td bgcolor="white" width="100%%">
    <textarea name="keywords" cols="60" rows="3">%(keywords)s</textarea>
  </td>
</tr>
		%(typeModule)s
		
		<% includeTpl('EventLocationInfo', parentRoomInfo=roomInfo(self._rh._target), modifying=False, showParent=True) %>


		%(boardModule)s
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Start Date")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="sDay" value="%(day)s" onChange="">-
                <input type="text" size="2" name="sMonth" value="%(month)s" onChange="">-
                <input type="text" size="4" name="sYear" value="%(year)s" onChange="">
                <input type="image" src=%(calendarIconURL)s alt="open calendar" border="0" onClick="javascript:window.open('%(calendarSelectURL)s?daystring=sDay&monthstring=sMonth&yearstring=sYear&month='+this.form.sMonth.value+'&year='+this.form.sYear.value+'&date='+this.form.sDay.value+'-'+this.form.sMonth.value+'-'+this.form.sYear.value,'calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <input type="text" size="2" name="sHour" value="%(sHour)s">:
                <input type="text" size="2" name="sMinute" value="%(sMinute)s">
		%(autoUpdate)s
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Duration")%></span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input type="text" size="2" name="durHours" value="%(durationHours)s">:
                <input type="text" size="2" name="durMins" value="%(durationMinutes)s">
            </td>
        </tr>
%(presenterFreeText)s
%(author)s
%(coauthor)s
%(presenter)s
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
