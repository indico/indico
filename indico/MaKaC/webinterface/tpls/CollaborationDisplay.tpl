<% if not OngoingBookings and not ScheduledBookings: %>
    <div class="collaborationDisplayTitle"><%= _("All video service events already finished.") %></div>
<% end %>

<% if OngoingBookings: %>
    <div class="groupTitleNoBorder collaborationDisplayTitle" style="margin-bottom: 5px;">Ongoing Today:</div>
<% end %>

<% for booking in OngoingBookings: %>
    <% includeTpl('BookingDisplay', Booking = booking, Kind = 'ongoing', Timezone = Timezone) %>
<% end %>


<% if ScheduledBookings: %>
    <div class="groupTitleNoBorder collaborationDisplayTitle">Upcoming:</div>
<% end %>

<% for date, bookings in ScheduledBookings: %>
    <div class="collaborationDisplayDateGroup">
        <div class="groupTitleSmallNoBackground" style="padding-left: 5px;">Scheduled for <%= formatDate (date, format = "%A %d/%m/%Y") %></div>
        <% for b in bookings: %>
            <% includeTpl('BookingDisplay', Booking = b, Kind = 'scheduled', Timezone = Timezone) %>
        <% end %>
    </div>
<% end %>