% if not OngoingBookings and not ScheduledBookings: 
    <div class="collaborationDisplayTitle">${ _("All video service events already finished.") }</div>
% endif

% if OngoingBookings: 
    <div class="groupTitleNoBorder collaborationDisplayTitle" style="margin-bottom: 5px;">Ongoing Today:</div>
% endif

% for booking in OngoingBookings: 
    <%include file="BookingDisplay.tpl" args="Booking = booking, Kind = 'ongoing', Timezone = Timezone"/>
% endfor


% if ScheduledBookings: 
    <div class="groupTitleNoBorder collaborationDisplayTitle">Upcoming:</div>
% endif

% for date, bookings in ScheduledBookings: 
    <div class="collaborationDisplayDateGroup">
        <div class="groupTitleSmallNoBackground" style="padding-left: 5px;">Scheduled for ${ formatDate (date, format = "%A %d/%m/%Y") }</div>
        % for b in bookings: 
            <%include file="BookingDisplay.tpl" args="Booking = b, Kind = 'scheduled', Timezone = Timezone"/>
        % endfor
    </div>
% endfor