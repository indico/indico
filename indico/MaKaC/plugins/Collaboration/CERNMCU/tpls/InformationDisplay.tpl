<table cellpadding="0" cellspacing="0">
    <tbody>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Name:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking._bookingParams["name"] }
            </td>
        </tr>
        % if Booking.getHasPin():
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('PIN:')}
            </td>
            % if Booking.getBookingParamByName("displayPin"):
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getPin() }
            </td>
            % else:
            <td class="collaborationConfDisplayInfoRightCol">
                ${ _("This conference is protected by a PIN.") }
            </td>
            % endif
        </tr>
        % endif
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Description:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking._bookingParams["description"] }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Participants:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                % if Booking.getParticipantList():
                    % for p in Booking.getParticipantList():
                        <div>${ p.getDisplayName(truncate=False) }</div>
                    % endfor
                % else:
                    ${ _("No participants yet.") }
                % endif
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('How to join:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <% bookingIdInMCU = str(Booking._bookingParams["id"]) %>
                <div>
                    ${ _('1) If you are registered in the CERN Gatekeeper, please dial ') }
                    ${ CERNGatekeeperPrefix }${ bookingIdInMCU } .
                </div>
                <div>
                    ${ _('2) If you have GDS enabled in your endpoint, please call ') }
                    ${ GDSPrefix }${ bookingIdInMCU } .
                </div>
                <div>
                    ${ _('3) Otherwise dial ') }
                    ${ MCU_IP}
                    ${ _(' and using FEC (Far-End Controls) with your remote, enter "') }
                    ${ bookingIdInMCU }
                    ${ _('" followed by the "#".') }
                </div>
                <div>
                    ${ _('4) To join by phone dial ') }
                    ${ Phone_number }
                    ${ _(' enter "') }
                    ${ bookingIdInMCU }
                    ${ _('" followed by the "#".') }
                </div>
            </td>
        </tr>
    </tbody>
</table>
