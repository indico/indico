<%page args="unrolledReservations=None, withPhoto=None"/>
<script type="text/javascript">
    function submit_rejection(url) {
        $('<form>', {
            method: 'POST',
            action: url
        }).submit();
    }

    function confirm_reject_occurrence(element, date)
    {
        var reason = prompt( 'Are you sure you want to REJECT the booking for '+date+'? If so, please give a reason:', '' );
        if (!reason)
            return false;

        submit_rejection(build_url(element.href, {reason: reason}));
        return false;
    }

    function confirm_reject_reservation(element, date)
    {
        var reason = prompt( 'Are you sure you want to REJECT the booking for '+date+'? If so, please give a reason:', '' );
        if (!reason)
            return false;

        submit_rejection(build_url(element.href, {reason: reason}));
        return false;
    }
</script>
% for collision in unrolledReservations:
    <%
    reservation = collision.withReservation if hasattr(collision, 'withReservation') else collision

    occurrence = collision
    myDetails = bookingDetailsUH.getURL( reservation )
    rejectOccurrence = urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( reservation, date=formatDate(occurrence.startDT.date(), format='yyyy/M/d') )
    rejectReservation = urlHandlers.UHRoomBookingRejectBooking.getURL( reservation )

    onClickDetails = ""
    height = "60" if withPhoto else "20"

    classText = 'class="rowPreB"' if not reservation.isConfirmed else ''


    onClickDetails = 'onclick="window.location=\'%s\'"' % myDetails
    canReject = reservation.canReject( user )

    occurrenceId = 'resv%s%s' % (reservation.id, occurrence.startDT)

    %>

    <tr class="resvHover${ classText }" style="height: ${ height }px; " id="${ occurrenceId }">

        % if withPhoto:
            <td ${onClickDetails} style="padding: 0px 10px 6px 0px; cursor: pointer;">
              % if reservation.room.photoId != None:
                  <img src="${ reservation.room.getSmallPhotoURL() }" />
              % endif
              % if reservation.room.photoId == None:
                  &nbsp;
              % endif
            </td>
        % endif
        <td ${onClickDetails} style="padding: 0px 10px 6px 0px; cursor: pointer;"><nobr>${ reservation.room.building }-${ reservation.room.floor }-${ reservation.room.roomNr }
            % if reservation.room.name != str(reservation.room.building) + '-' + str(reservation.room.floor) + '-' + str(reservation.room.roomNr):
                <small>(${ reservation.room.name })</small>
            % endif
            </nobr>
        </td>
        <td ${onClickDetails} style="padding: 0px 10px 6px 0px; cursor: pointer;">${ str( reservation.reason ) + "<br />" + str( reservation.bookedForName ) }</td>
        <td ${onClickDetails} style="padding: 0px 10px 6px 0px; cursor: pointer;">
            ${ formatDate(occurrence.startDT.date()) }
        </td>
        <td ${onClickDetails} style="padding: 0px 10px 6px 0px; cursor: pointer;">${ verbose_t( reservation.startDT.time() ) }<br />${ verbose_t( reservation.endDT.time() ) }</td>
        <td style="padding: 0px 10px 6px 0px;">
            % if canReject and not reservation.isCancelled and not reservation.isRejected:
                % if reservation.repeatability != None:
                    <a href="${ rejectOccurrence }" onclick="return confirm_reject_occurrence(this, '${ occurrence.startDT }');" >${ _("reject")}</a><br />
                % else:
                    <a href="${ rejectReservation }" onclick="return confirm_reject_reservation(this, '${ occurrence.startDT }');" >${ _("reject")}</a><br />
                % endif
            % endif
        </td>
    </tr>
% endfor
