<form id="BreakDataModificationForm" method="POST" action=%(postURL)s>
<table width="60%%" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px;">
        <tr>
            <td class="groupTitle" colspan="2">%(WPtitle)s</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Title")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" name="title" size="60" value=%(title)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Description")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <textarea name="description" cols="60" rows="6">%(description)s</textarea>
            </td>
        </tr>
	<tr>


        <% includeTpl('EventLocationInfo', event=self._rh._break, modifying=True, parentRoomInfo=roomInfo(self._rh._break, level='inherited'), showParent=True) %>

	</tr>       
	<tr>
            <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Start date")%></span></td>
            <td bgcolor="white" width="100%%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="<%= sDay %>" name="sDay" id="sDay"/>                                       
                <input type="hidden" value="<%= sMonth %>" name="sMonth" id="sMonth"/>
                <input type="hidden" value="<%= sYear %>" name="sYear" id="sYear"/>   
                <input type="hidden" value="<%= sHour %>" name="sHour" id="sHour" />
                <input type="hidden" value="<%= sMinute %>" name="sMinute" id="sMinute" />
		%(autoUpdate)s
                %(schOptions)s
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> <%= _("Duration")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="2" name="durHours" 
                    value=%(durationHours)s>:
                <input type="text" size="2" name="durMins" 
                    value=%(durationMinutes)s>
            </td>
        </tr>
%(Colors)s
        <tr align="center">
            <td colspan="2" class="buttonBar" valign="bottom" align="center">
		<input type="submit" class="btn" name="OK" value="<%= _("ok")%>">
		<input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
IndicoUI.executeOnLoad(function()
    {   
        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);
       
        <% if sDay != '': %>
            startDate.set('<%= sDay %>/<%= sMonth %>/<%= sYear %><%= " " %><%if len (sHour) == 1:%>0<%= sHour %><%end%><%else:%><%= sHour %><%end%>:<% if len (sMinute) == 1:%>0<%= sMinute %><%end%><%else:%><%= sMinute %><%end%>');
        <% end %>        
    });       
injectValuesInForm($E('BreakDataModificationForm'));

</script>
