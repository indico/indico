<table>
    <tbody>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Name')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking._bookingParams["name"] %>
            </td>
        </tr>
        <% if Booking.getHasPin(): %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Protection')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= _("This conference is protected by a PIN.") %>
            </td>
        </tr>
        <% end %>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Description')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <%= Booking._bookingParams["description"] %>
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('Participants')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <% if Booking.getParticipantList(): %>
                    <% for p in Booking.getParticipantList(): %>
                        <div><%= p.getDisplayName() %></div>
                    <% end %>
                <% end %>
                <% else: %>
                    <%= _("No participants yet.") %>
                <% end %>
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span><%= _('How to join')%>:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <% bookingIdInMCU = str(Booking._bookingParams["id"]) %>
                <div>
                    <%= _('1) If you are registered in the CERN Gatekeeper, please dial ') %>
                    <%= CERNGatekeeperPrefix %><%= bookingIdInMCU %> .
                </div>
                <div>
                    <%= _('2) If you have GDS enabled in your endpoint, please call ') %>
                    <%= GDSPrefix %><%= bookingIdInMCU %> .
                </div>
                <div>
                    <%= _('3) Otherwise dial ') %>
                    <%= MCU_IP%>
                    <%= _(' and using FEC (Far-End Controls) with your remote, enter "') %>
                    <%= bookingIdInMCU %>
                    <%= _('" followed by the "#".') %>
                </div>
                <div>
                    <%= _('4) To join by phone dial ') %>
                    <%= Phone_number %>
                    <%= _(' enter "') %>
                    <%= bookingIdInMCU %>
                    <%= _('" followed by the "#".') %>
                </div>
            </td>
        </tr>
    </tbody>
</table>
