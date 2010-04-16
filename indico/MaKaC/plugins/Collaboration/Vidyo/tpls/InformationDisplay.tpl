<table cellpadding="0" cellspacing="0">
    <tbody>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <%= _('Room Name:')%>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getBookingParamByName("roomName") %>
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <%= _('Extension:')%>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getExtension() %>
            </td>
        </tr>
        <% if Booking.getHasPin(): %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <%= _('PIN:')%>
            </td>
            <% if Booking.getBookingParamByName("displayPin"): %>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getPin() %>
            </td>
            <% end %>
            <% else: %>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= _("This Vidyo room is protected by a PIN.") %>
            </td>
            <% end %>
        </tr>
        <% end %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <%= _('Owner:')%>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getOwnerObject().getFullName() %>
            </td>
        </tr>
        <% if Booking.getBookingParamByName("displayURL"): %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <%= _('Auto-join URL:')%>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getURL() %>
            </td>
        </tr>
        <% end %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Description')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking.getBookingParamByName("roomDescription") %>
            </td>
        </tr>
    </tbody>
</table>
