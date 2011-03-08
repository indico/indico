<% from MaKaC.common.timezoneUtils import getAdjustedDate %>

<div>
    ${ _("Note: times are shown in the server timezone: ") + ServerTZ }
</div>

<div style="padding-top: 15px;font-size:15px;">
    ${ _("We will delete rooms in events that finish before: ") + formatDateTime(getAdjustedDate(MaxDate, tz=ServerTZ)) }.<br &>
    ${ _("There are ") + str(TotalRoomCount) + _(" rooms in total.") }
</div>

<div style="padding-top: 30px;font-size:15px;">${ _("Vidyo rooms that would be deleted") }:</div>
${ OldBookings }

<div style="padding-top: 30px;font-size:15px;">${ _("Vidyo rooms that would NOT be deleted") }:</div>
${ NewBookings }

