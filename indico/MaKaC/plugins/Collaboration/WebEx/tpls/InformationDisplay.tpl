<table>
    <tbody>
        <% if Booking.getHasAccessPassword(): %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Protection')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= _("This WebEx meeting is protected by a password.") %>      
            </td>
        </tr>
        <% end %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Description')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking._bookingParams["meetingDescription"] %>      
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Join URL')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <a href="<%= Booking._url %>" target="_blank" ><%= Booking._url %></a>
            </td>
        </tr>
    </tbody>
</table>
