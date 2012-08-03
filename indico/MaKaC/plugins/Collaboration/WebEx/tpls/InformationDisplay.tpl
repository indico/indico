<table>
    <tbody>
        % if Booking.getHasAccessPassword():
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Protection:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                This WebEx meeting is protected by a password.
            </td>
        </tr>
        % endif
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Agenda:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking._bookingParams["meetingDescription"] }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Toll free call in number:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getPhoneNum() }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Toll call in number:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getPhoneNumToll() }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Call in access code:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                ${ Booking.getPhoneAccessCode() }
            </td>
        </tr>
        <tr>
            <td class="collaborationConfDisplayInfoLeftCol">
                <span>Join URL:</span>
            </td>
            <td class="collaborationConfDisplayInfoRightCol">
                <a href="${ Booking.getUrl() }" target="_blank" >${ Booking.getUrl() }</a>
            </td>
        </tr>
    </tbody>
</table>
