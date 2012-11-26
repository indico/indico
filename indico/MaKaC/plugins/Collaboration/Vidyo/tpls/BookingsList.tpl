<% from MaKaC.common.timezoneUtils import unixTimeToDatetime %>

<ul>

<% isEmpty = True %>
<% totalCount = 0 %>
% for key, bookingsList in BookingsPerConfIterator.iteritems():
    <% isEmpty = False %>
    <li>
        ${ _("Ending on: ") + formatDateTime(unixTimeToDatetime(key, tz=ServerTZ), showWeek = True) }
    <ul>
    <% bookingsList = bookingsList.items() %>
    <% bookingsList.sort(key = PairSorter) %>
    % for conf, nBookings in bookingsList:
        <% totalCount = totalCount + nBookings %>
        <li>${ _("Inside conference: ") + conf.getTitle() + ", " + str(nBookings) + _(" Vidyo bookings.") }</li>
    % endfor
    </ul>
    </li>
% endfor

% if isEmpty:
    <li>${ _("No Vidyo rooms") }</li>
% else:
    <li>${ str(totalCount) + _(" bookings in total.") }</li>
% endif

</ul>
