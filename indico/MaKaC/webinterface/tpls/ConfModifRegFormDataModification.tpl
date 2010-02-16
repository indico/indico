
<script type="text/javascript">
  // ---- On Load
    IndicoUI.executeOnLoad(function()
    {

        var startDate = IndicoUI.Widgets.Generic.dateField(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);

        var medDate = IndicoUI.Widgets.Generic.dateField(false,null,['meDay', 'meMonth', 'meYear']);
        $E('meDatePlace').set(medDate);

        <% if sDay != '': %>
            startDate.set('<%= sDay %>/<%= sMonth %>/<%= sYear %>');
        <% end %>

        <% if eDay != '': %>
            endDate.set('<%= eDay %>/<%= eMonth %>/<%= eYear %>');
        <% end %>

        <% if meDay != '': %>
            medDate.set('<%= meDay %>/<%= meMonth %>/<%= meYear %>');
        <% end %>

     });

</script>

<form name="DataModif" method="POST" action="%(postURL)s">
  <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle" colspan="2"> <%= _("Modify registration form")%></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Start date")%></span></td>
      <td bgcolor="white" width="100%%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="<%= sDay %>" name="sDay" id="sDay"/>
                <input type="hidden" value="<%= sMonth %>" name="sMonth" id="sMonth"/>
                <input type="hidden" value="<%= sYear %>" name="sYear" id="sYear"/>
       </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("End date")%></span></td>
      <td bgcolor="white" width="100%%">
                <span id="eDatePlace"></span>
                <input type="hidden" value="<%= eDay %>" name="eDay" id="eDay"/>
                <input type="hidden" value="<%= eMonth %>" name="eMonth" id="eMonth"/>
                <input type="hidden" value="<%= eYear %>" name="eYear" id="eYear"/>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Modification End date")%></span></td>
      <td bgcolor="white" width="100%%">
                <span id="meDatePlace"></span>
                <input type="hidden" value="<%= meDay %>" name="meDay" id="meDay"/>
                <input type="hidden" value="<%= meMonth %>" name="meMonth" id="meMonth"/>
                <input type="hidden" value="<%= meYear %>" name="meYear" id="meYear"/>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
      <td bgcolor="white" width="100%%"><input type="text" size="50" name="title" value="%(title)s"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Announcement")%></span></td>
      <td bgcolor="white" width="100%%"><textarea name="announcement" cols="100" rows="10">%(announcement)s</textarea></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Max No. of registrants")%></span></td>
      <td bgcolor="white" width="100%%"><input type="text" size="50" name="usersLimit" value="%(usersLimit)s"> <%= _("(0 or nothing for unlimited)")%></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Contact info")%></span></td>
      <td bgcolor="white" width="100%%"><input type="text" size="50" name="contactInfo" value="%(contactInfo)s"></td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email Notification")%></span></td>
      <td bgcolor="white" width="100%%">
        <table align="left">
        <tr>
          <td align="right">
          <b> <%= _("To List")%>:&nbsp;</b>
          </td>
          <td align="left">
          <input type="text" size="50" name="toList" value="%(toList)s">
          </td>
        </tr>
        <tr>
          <td>
          <b> <%= _("Cc List")%>:&nbsp;</b>
          </td>
          <td align="left">
          <input type="text" size="50" name="ccList" value="%(ccList)s">
          </td>
        </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Must have an account")%></span></td>
      <td bgcolor="white" width="100%%"><input type="checkbox" size="50" name="mandatoryAccount" %(mandatoryAccount)s> ( <%= _("Uncheck if an account is not needed")%>)</td>
    </tr>

    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Currency")%></span></td>
      <td bgcolor="white" >%(Currency)s</td>
    </tr>

    <tr><td>&nbsp;</td></tr>
    <tr>
      <td colspan="2" align="left">
        <table align="left">
          <tr>
            <td><input type="submit" class="btn" value="<%= _("ok")%>"></td>
            <td><input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel"></td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</form>
