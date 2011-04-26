<table cellpadding="0" cellspacing="0">
    <tbody>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Title:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking._bookingParams["meetingTitle"] }
            </td>
        </tr>

        % if Booking.getHasAccessPassword():
            % if not Booking.getBookingParamByName("displayPassword") and not Booking.getBookingParamByName("displayPhonePassword"):
            <tr>
                <td class="collaborationConfDisplayInfoLeftCol">
                    ${ _('Password:')}
                </td>
                <td class="collaborationConfDisplayInfoRightCol">
                    ${ _("This EVO meeting is protected by a private password.") }
                </td>
            </tr>
            % else:
                % if Booking.getBookingParamByName("displayPassword"):
                <tr>
                    <td class="collaborationConfDisplayInfoLeftCol">
                        ${ _('Password:')}
                    </td>
                    <td class="collaborationConfDisplayInfoRightCol">
                        ${ Booking.getAccessPassword() }
                    </td>
                </tr>
                % endif
                % if Booking.getBookingParamByName("displayPhonePassword"):
                <tr>
                    <td class="collaborationConfDisplayInfoLeftCol">
                        ${ _('Phone Bridge Password:')}
                    </td>
                    <td class="collaborationConfDisplayInfoRightCol">
                        ${ Booking.getPhoneBridgePassword() }
                    </td>
                </tr>
                % endif
            % endif
        % endif

        % if Booking.getBookingParamByName("displayPhoneBridgeNumbers"):
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Phone bridge numbers:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <a target="_blank" href="${ ListOfPhoneBridgeNumbersURL}">
                    ${ _('List of phone bridge numbers')}
                </a>
            </td>
        </tr>
        % endif

        % if Booking.getBookingParamByName("displayURL"):
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Auto-join URL:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <a href="${ Booking.getUrl() }">${ Booking.getUrl() }</a>
            </td>
        </tr>
        % endif

        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Description:')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking._bookingParams["meetingDescription"] }
            </td>
        </tr>
    </tbody>
</table>
