<%inherit file="/ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <script type="text/javascript">
      var bookings = ${dict((b['id'], b) for b in all_bookings)|n,j};
    </script>


    % if not all_bookings:
        <div class="collaborationDisplayTitle">${ _("There are no bookings associated with this event.") }</div>
    % endif

    % if OngoingBookings or timeless_bookings:
        <div class="groupTitleNoBorder collaborationDisplayTitle" style="margin-bottom: 5px;">Active bookings</div>

        % for booking in OngoingBookings:
            <%include file="BookingDisplay.tpl" args="Booking = booking, Kind = 'ongoing', Timezone = Timezone"/>
        % endfor

        % for booking in timeless_bookings:
            <%include file="BookingDisplay.tpl" args="Booking = booking, Kind = 'timeless', Timezone = Timezone"/>
        % endfor
    % endif


    % if ScheduledBookings:
        <div class="groupTitleNoBorder collaborationDisplayTitle">Upcoming</div>

        % for date, bookings in ScheduledBookings:
        <div class="collaborationDisplayDateGroup">
            <div class="groupTitleSmallNoBackground" style="padding-left: 5px;">Scheduled for ${ formatDate (date, format = "%A %d/%m/%Y") }</div>
            % for b in bookings:
                <%include file="BookingDisplay.tpl" args="Booking = b, Kind = 'scheduled', Timezone = Timezone"/>
            % endfor
        </div>
        % endfor
    % endif
</%block>
