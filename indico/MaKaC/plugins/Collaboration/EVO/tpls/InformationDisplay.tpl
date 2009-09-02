<table>
    <tbody>
        <% if Booking.getHasAccessPassword(): %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Protection')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= _("This EVO meeting is protected by a password.") %>      
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
    </tbody>
</table>