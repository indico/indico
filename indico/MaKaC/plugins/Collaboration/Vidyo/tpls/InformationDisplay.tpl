<table cellpadding="0" cellspacing="0">
    <tbody>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Room Name')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getBookingParamByName("roomName") }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Extension')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getExtension() }
            </td>
        </tr>
        % if Booking.getHasPin():
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Meeting PIN')}
            </td>
            % if Booking.getBookingParamByName("displayPin"):
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getPin() }
            </td>
            % else:
            <td class="collaborationConfDisplayInfoRightCol">
                ${ _("This Vidyo room is protected by a PIN.") }
            </td>
            % endif
        </tr>
        % endif
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Moderator')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <div style="display:inline">${ Booking.getOwnerObject().getStraightFullName() }</div>
                % if Booking.getConference().canModify(self_._rh._aw) and Booking.getOwner()["id"] != self_._rh._getUser().getId():
                    <div style="display:inline"><a href="#" style="font-size:12px" onClick= "makeMeModerator(this,${Booking.getConference().getId()},${Booking.getId()}, successMakeEventModerator)">${_("Make me moderator")}</a></div>
                % endif
            </td>
        </tr>


        % if Booking.getBookingParamByName("displayURL"):
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Auto-join URL')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <a href="${ Booking.getURL() }">${ Booking.getURL() }</a>
            </td>
        </tr>
        % endif
        % if Booking.getBookingParamByName("displayPhoneNumbers") and PhoneNumbers:
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                ${ _('Phone access numbers')}
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <ul style="margin: 0;">
                    ${ '<li>' + '</li><li>'.join(PhoneNumbers) + '</li>' }
                </ul>
            </td>
        </tr>
        % endif
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>${ _('Description')}</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getBookingParamByName("roomDescription") }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>${ _('Linked to')}</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getLinkVideoText() }
            </td>
        </tr>
    </tbody>
</table>
