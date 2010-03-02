<form id="eventModificationForm" action="%(postURL)s" method="POST">
    %(locator)s
    <input type="hidden" name="event_type" value="%(event_type)s">
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle"><%= _("Modify event data")%></div></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
            <td bgcolor="white" width="100%%">
                    <input type="text" name="title" size="80" value=%(title)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
            <td bgcolor="white" width="100%%">
                <textarea name="description" cols="70" rows="12" wrap="soft">%(description)s</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Keywords<br><small>( <%= _("one per line")%>)</small></span></td>
            <td bgcolor="white" width="100%%">
                <textarea name="keywords" cols="70" rows="3">%(keywords)s</textarea>
            </td>
        </tr>

	<% includeTpl('EventLocationInfo', event=self._rh._target, modifying=True, showParent=False) %>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Start date")%></span></td>
            <td bgcolor="white" width="100%%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="<%= sDay %>" name="sDay" id="sDay"/>
                <input type="hidden" value="<%= sMonth %>" name="sMonth" id="sMonth"/>
                <input type="hidden" value="<%= sYear %>" name="sYear" id="sYear"/>
                <input type="hidden" value="<%= sHour %>" name="sHour" id="sHour" />
                <input type="hidden" value="<%= sMinute %>" name="sMinute" id="sMinute" />
                &nbsp;<input type="checkbox" name="move" value="1" checked>  <%= _("move timetable content")%>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("End date")%></span></td>
            <td bgcolor="white" width="100%%">
                <span id="eDatePlace"></span>
                <input type="hidden" value="<%= eDay %>" name="eDay" id="eDay"/>
                <input type="hidden" value="<%= eMonth %>" name="eMonth" id="eMonth"/>
                <input type="hidden" value="<%= eYear %>" name="eYear" id="eYear"/>
                <input type="hidden" value="<%= eHour %>" name="eHour" id="eHour" />
                <input type="hidden" value="<%= eMinute %>" name="eMinute" id="eMinute" />
            </td>
        </tr>
        <!-- Fermi timezone awareness -->
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Timezone</span></td>
            <td bgcolor="white" width="100%%">
              <select name="Timezone">
              %(timezoneOptions)s
              </select>
            </td>
        </tr>
        <!-- Fermi timezone awareness(end) -->
%(additionalInfo)s
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Support caption")%></span></td>
            <td bgcolor="white" width="100%%"><input type="text" name="supportCaption" value=%(supportCaption)s size="50"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Support email")%></span></td>
            <td bgcolor="white" width="100%%"><input type="text" name="supportEmail" value=%(supportEmail)s size="50"></td>
        </tr>
        <!-- TO REMOVE CHAIRPERSON TEXT -->
        <% if conference.getType() != "simple_event": %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Chairperson text")%></span></td>
            <td bgcolor="white" width="100%%">
                <input type="text" name="chairText" value=%(chairText)s size="50">
            </td>
        </tr>
        <% end %>
        <% if conference.getType() == "simple_event": %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Organisers</span></td>
            <td bgcolor="white" width="100%%">
                <input type="text" name="orgText" value=%(orgText)s size="50">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Internal Comments</span></td>
            <td bgcolor="white" width="100%%">
                <textarea name="comments" cols=50 rows=5><%= conference.getComments() %></textarea>
            </td>
        </tr>
        <% end %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Timetable default style")%></span></td>
            <td bgcolor="white" width="100%%"><select name="defaultStyle">%(styleOptions)s</select></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Visibility")%></span></td>
            <td bgcolor="white" width="100%%">
              <select name="visibility">
              %(visibility)s
              </select>
	    </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Event type")%></span></td>
            <td bgcolor="white" width="100%%">
              <select name="eventType">
              %(types)s
              </select>
	    </td>
        </tr>
        <% if Config.getInstance().getShortEventURL() != "" : %>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Short URL tag</span></td>
            <td bgcolor="white" width="100%%">
               <span class="blacktext"><em> <%=Config.getInstance().getShortEventURL() %></em></span><input type="text" name="shortURLTag" value=%(shortURLTag)s size="30">
            </td>
        </tr>
        <% end %>
        <tr align="left">
            <td align="center" width="100%%" colspan="2" class="buttonBar">
		<input type="submit" class="btn" value="<%= _("ok")%>">
		<input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel">
            </td>
        </tr>
    </table>
</form>

<script  type="text/javascript">

        IndicoUI.executeOnLoad(function()
	{

        var startDate = IndicoUI.Widgets.Generic.dateField(true,null,['sDay', 'sMonth', 'sYear','sHour', 'sMinute']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(true,null,['eDay', 'eMonth', 'eYear', 'eHour', 'eMinute']);
        $E('eDatePlace').set(endDate);

        <% if sDay != '': %>
            startDate.set('<%= sDay %>/<%= sMonth %>/<%= sYear %><%= " " %><%if len (sHour) == 1:%>0<%= sHour %><%end%><%else:%><%= sHour %><%end%>:<% if len (sMinute) == 1:%>0<%= sMinute %><%end%><%else:%><%= sMinute %><%end%>');
        <% end %>

        <% if eDay != '': %>
            endDate.set('<%= eDay %>/<%= eMonth %>/<%= eYear %><%= " " %><%if len (eHour) == 1:%>0<%= eHour %><%end%><%else:%><%= eHour %><%end%>:<% if len (eMinute) == 1:%>0<%= eMinute %><%end%><%else:%><%= eMinute %><%end%>');
        <% end %>

		injectValuesInForm($E('eventModificationForm'));
	});
</script>
