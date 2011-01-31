<%= description %>
<table class="conferenceDetails">
    <tr>
        <td colspan="2"><br></td>
    </tr>
    <tr>
        <td align="right" valign="top" class="displayField"><b> <%= _("Dates")%>:</b></td>
        <td><%= dateInterval %></td>
    </tr>
    <tr>
        <td align="right" valign="top" class="displayField"><b> <%= _("Timezone")%>:</b></td>
        <td><%= timezone %></td>
    </tr>
    <tr>
        <td align="right" valign="top" class="displayField"><b> <%= _("Location")%>:</b></td>
        <td><%= location %></td>
    </tr>
    <%= chairs %>
    <%= material %>
    <%= moreInfo %>
</table>
<%= actions %>
