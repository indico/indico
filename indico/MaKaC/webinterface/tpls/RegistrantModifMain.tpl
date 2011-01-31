<table width="90%" align="left" border="0">
  <tr>
    <td>
      <table width="100%" align="left" border="0">
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Registrant ID")%></span></td>
          <td bgcolor="white"><%= id %></td>
          <form action=<%= dataModificationURL %> method="POST">
            <td rowspan="14" valign="bottom" align="right" width="1%"><input type="submit" class="btn" value="<%= _("modify")%>"></td>
          </form>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
          <td bgcolor="white" class="blacktext"><%= title %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Family Name")%></span></td>
          <td bgcolor="white" class="blacktext"><b><%= familyName %></b></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("First Name")%></span></td>
          <td bgcolor="white" class="blacktext"><%= firstName %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Position")%></span></td>
          <td bgcolor="white" class="blacktext"><%= position %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Institution")%></span></td>
          <td bgcolor="white" class="blacktext"><%= institution %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Address")%></span></td>
          <td bgcolor="white" class="blacktext"><%= address %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("City")%></span></td>
          <td bgcolor="white" class="blacktext"><%= city %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Country")%></span></td>
          <td bgcolor="white" class="blacktext"><%= country %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Phone")%></span></td>
          <td bgcolor="white" class="blacktext"><%= phone %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Fax")%></span></td>
          <td bgcolor="white" class="blacktext"><%= fax %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Email")%></span></td>
          <td bgcolor="white" class="blacktext"><%= email %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Personal Homepage")%></span></td>
          <td bgcolor="white" class="blacktext"><%= personalHomepage %></td>
        </tr>
        <tr>
          <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Registration date")%></span></td>
          <td bgcolor="white" class="blacktext"><%= registrationDate %></td>
        </tr>
        <tr>
          <td colspan="3" class="horizontalLine">&nbsp;</td>
        </tr>
        <%= sections %>
        <%= statuses %>
        <%= transaction %>
      </table>
    </td>
  </tr>
</table>