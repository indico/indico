<form id="ContributionDataModificationForm" method="POST" action="%(postURL)s">
    <table width="60%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Edit contribution data")%></td>
        </tr>
        <tr>
            <td class="titleCellTD">
                <span class="titleCellFormat"><%= _("Title")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" name="title" size="80" value=%(title)s />
            </td>
        </tr>
        <%
        if self._rh._target.getConference().getAbstractMgr().isActive() and self._rh._target.getConference().hasEnabledSection("cfa") and self._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
        %>
        %(additionalFields)s
        <%end%>
        <%
            else:
        %>
        <tr>
            <td class="titleCellTD">
                <span class="titleCellFormat"><%= _("Description")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <textarea name="description" cols="80" rows="6" wrap="soft">%(description)s</textarea>
            </td>

        </tr>
        <%end%>
	<tr>
	  <td style="text-align: right;">
	    <span class="titleCellFormat"><%= _("Date/Time")%></span>
	  </td>
	  <td><span id="dateTime"></span></td>
	</tr>
	<tr>
	  <td style="text-align: right;">
	    <span class="titleCellFormat"><%= _("Duration")%></span>
	  </td>
	  <td><span id="duration"></span></td>
	</tr>
        <% includeTpl('EventLocationInfo', event=self._rh._target, modifying=True, parentRoomInfo=roomInfo(self._rh._target, level='inherited'), showParent=True) %>


	%(Board)s
	%(Type)s
        <tr>
          <td class="titleCellTD">
            <span class="titleCellFormat"><%= _("Keywords")%><br><small>( <%= _("one per line")%>)</small></span>
          </td>
          <td bgcolor="white" width="100%%" valign="top" class="blacktext">
            <textarea name="keywords" cols="60" rows="6">%(keywords)s</textarea>
          </td>
        </tr>
        <tr align="center">
          <td colspan="2" class="buttonBar" valign="bottom" align="center">
	    <input type="submit" class="btn" value="<%= _("ok")%>" name="ok" />
	    <input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel" />
          </td>
        </tr>
    </table>
</form>

<script type="text/javascript">

<% if contrib.isScheduled(): %>
var dateTime = IndicoUI.Widgets.Generic.dateField(true, {name: 'dateTime'});
dateTime.set('<%= dateTime %>');
$E('dateTime').set(dateTime)
<% end %>
<% else: %>
$E('dateTime').set('Not scheduled')
<% end %>

var duration = IndicoUI.Widgets.Generic.durationField('<%= duration %>', {name: 'duration'});
$E('duration').set(duration)

injectValuesInForm($E('ContributionDataModificationForm'));

</script>
