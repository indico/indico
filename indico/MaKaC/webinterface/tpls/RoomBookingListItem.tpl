<script type="text/javascript">
    function confirm_reject_occurrence(element, date)
    {
        var reason = prompt( 'Are you sure you want to REJECT the booking for '+date+'? If so, please give a reason:', '' );
        if ( reason == null )
            return false;

        element.href = element.href + '&reason=' + encodeURI( reason );
		return true;
    }

	function confirm_reject_reservation(date)
    {
		return confirm( 'Are you sure you want to REJECT the booking for '+date+'? If so, please give a reason:', '' );
    }
</script>
<%
myDetails = bookingDetailsUH.getURL( reservation )
rejectOccurrence = urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( reservation, formatDate(occurrence.startDT.date()) )
rejectReservation = urlHandlers.UHRoomBookingRejectBooking.getURL( reservation )

onClickDetails = ""
height = "20"

if withPhoto:
    height = "60"

classText = ''

if not reservation.isConfirmed:
    classText = 'class="rowPreB"'


onClickDetails = 'onclick="window.location=\'%s\'"' % myDetails
canReject = reservation.canReject( user )

occurrenceId = 'resv%s%s' % (reservation.id, occurrence.startDT)

%>
<% end %>
<% end %>


<tr <%= classText %> style="height: <%= height %>px; " id="<%= occurrenceId %>" onmouseover="handleMouseOverResv( '<%= occurrenceId %>' )" onmouseout="handleMouseOutResv( '<%= occurrenceId %>' )" >

    <% if withPhoto: %>
        <td <%=onClickDetails%> style="padding: 0px 10px 6px 0px; cursor: pointer;">
          <% if reservation.room.photoId != None: %>
              <img src="<%= reservation.room.getSmallPhotoURL() %>" />
          <% end %>
          <% if reservation.room.photoId == None: %>
              &nbsp;
          <% end %>
        </td>
    <% end %>
    <td <%=onClickDetails%> style="padding: 0px 10px 6px 0px; cursor: pointer;"><nobr><%= reservation.room.building %>-<%= reservation.room.floor %>-<%= reservation.room.roomNr %>
        <% if reservation.room.name != str(reservation.room.building) + '-' + str(reservation.room.floor) + '-' + str(reservation.room.roomNr): %>
            <small>(<%= reservation.room.name %>)</small>
        <% end %>
        </nobr>
    </td>
    <td <%=onClickDetails%> style="padding: 0px 10px 6px 0px; cursor: pointer;"><%= str( reservation.reason ) + "<br />" + str( reservation.bookedForName ) %></td>
    <td <%=onClickDetails%> style="padding: 0px 10px 6px 0px; cursor: pointer;">
        <%= formatDate(occurrence.startDT.date()) %>
    </td>
    <td <%=onClickDetails%> style="padding: 0px 10px 6px 0px; cursor: pointer;"><%= verbose_t( reservation.startDT.time() ) %><br /><%= verbose_t( reservation.endDT.time() ) %></td>
    <td style="padding: 0px 10px 6px 0px;">
        <% if canReject and not reservation.isCancelled and not reservation.isRejected: %>
			<% if reservation.repeatability != None: %>
            	<a href="<%= rejectOccurrence %>" onclick="return confirm_reject_occurrence(this, '<%= occurrence.startDT %>');" ><%= _("reject")%></a><br />
			<% end %>
			<% else: %>
				<a href="<%= rejectReservation %>" onclick="return confirm_reject_reservation('<%= occurrence.startDT %>');" ><%= _("reject")%></a><br />
			<% end %>
        <% end %>
    </td>
</tr>
