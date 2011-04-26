<% from MaKaC.common.timezoneUtils import getAdjustedDate %>

<div>
    % if Error:
        ${ _("Not all rooms could be deleted due to the following error: ") + escape(str(Error)) }<br />
        ${ _("All rooms before ") + formatDateTime(getAdjustedDate(MaxDate, tz=ServerTZ)) + _(" should have been deleted but only the date ") + formatDateTime(getAdjustedDate(AttainedDate, tz=ServerTZ)) + _(" was reached.") }
    % else:
        ${ _("All rooms before ") + formatDateTime(getAdjustedDate(MaxDate, tz=ServerTZ)) + _(" were deleted.") }<br />
    % endif
    ${ str(PreviousTotal - NewTotal) + _(" Vidyo rooms were deleted in Vidyo.") }<br />
    ${ _("There were ") + str(PreviousTotal) + _(" rooms before the operation and there are ") + str(NewTotal) + _(" rooms left now.") }<br />
</div>
