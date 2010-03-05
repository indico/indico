
<form method="POST" action="%(postURL)s">
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Modify call for abstract data")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Start date")%></span></td>
             <td bgcolor="white" width="100%%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="<%= sDay %>" name="sDay" id="sDay"/>
                <input type="hidden" value="<%= sMonth %>" name="sMonth" id="sMonth"/>
                <input type="hidden" value="<%= sYear %>" name="sYear" id="sYear"/>
       </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("End date")%></span></td>
            <td bgcolor="white" width="100%%">
                <span id="eDatePlace"></span>
                <input type="hidden" value="<%= eDay %>" name="eDay" id="eDay"/>
                <input type="hidden" value="<%= eMonth %>" name="eMonth" id="eMonth"/>
                <input type="hidden" value="<%= eYear %>" name="eYear" id="eYear"/>
        </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Modification deadline")%></span></td>
            <td bgcolor="white" width="100%%">
                <span id="mDatePlace"></span>
                <input type="hidden" value="<%= mDay %>" name="mDay" id="mDay"/>
                <input type="hidden" value="<%= mMonth %>" name="mMonth" id="mMonth"/>
                <input type="hidden" value="<%= mYear %>" name="mYear" id="mYear"/>
        </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Announcement")%></span></td>
            <td bgcolor="white" width="100%%"><textarea name="announcement" rows="10" cols="60">%(announcement)s</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email Notification on Submission")%></span></td>
            <td bgcolor="white" width="100%%">
              <table align="left">
                <tr>
                  <td align="right">
                    <b> <%= _("To List")%>:&nbsp;</b>
                  </td>
                  <td align="left">
                    <input type="text" size="50" name="toList" value="%(toList)s">
                  </td>
                <tr>
                  <td>
                    <b> <%= _("Cc List")%>:&nbsp;</b>
                  </td>
                  <td align="left">
                    <input type="text" size="50" name="ccList" value="%(ccList)s">
                  </td>
                </tr>
                <tr><td colspan="2"><small>( <%= _("You can write several email addresses separated by commas")%>)</small></td></tr>
              </table>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left">
                <table align="left">
                    <tr>
                        <td><input type="submit" class="btn" value="<%= _("ok")%>"></td>
                        <td><input type="submit" class="btn" value="<%= _("cancel")%>" name=" <%= _("cancel")%>"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
// ---- On Load
    IndicoUI.executeOnLoad(function()
    {

        var startDate = IndicoUI.Widgets.Generic.dateField(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);

        var modDate = IndicoUI.Widgets.Generic.dateField(false,null,['mDay', 'mMonth', 'mYear']);
        $E('mDatePlace').set(modDate);

        <% if sDay != '': %>
            startDate.set('<%= sDay %>/<%= sMonth %>/<%= sYear %>');
        <% end %>

        <% if eDay != '': %>
            endDate.set('<%= eDay %>/<%= eMonth %>/<%= eYear %>');
        <% end %>

        <% if mDay != '': %>
            modDate.set('<%= mDay %>/<%= mMonth %>/<%= mYear %>');
        <% end %>

     });

</script>

