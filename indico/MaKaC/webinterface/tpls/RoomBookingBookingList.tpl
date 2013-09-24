<table cellpadding="0" cellspacing="0" border="0" width="80%">
    <tr>
    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td>
    </tr>
    <tr>
        <td class="bottomvtab" width="100%">
            <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                <tr>
                    <td class="maincell" >
                        <div style="float: left; width: 820px; margin-left: 15px">
                        % if newBooking:
                        <ul id="breadcrumbs" style="margin:0px 0px 20px -15px; padding: 0; list-style: none;">
                            <li><span><a href="${ urlHandlers.UHRoomBookingBookRoom.getURL() }">${_("Specify Search Criteria")}</a></span></li>
                            <li><span class="current">${_("Select Available Period")}</span></li>
                            <li><span>${_("Confirm Reservation")}</span></li>
                        </ul>
                        % else :
                            <h2 class="page_title">
                            % if not title:
                                <!-- Generic title -->
                                ${ numResvs } ${ _("Booking(s) found")}:
                            % elif title:
                                ${ title }
                            % endif
                            </h2>
                            % if prebookingsRejected:
                                <br /><br />
                                <span class="actionSucceeded">${ subtitle }</span>
                                <p style="margin-left: 6px;">${ description }</p>
                            % endif
                        % endif
                        <div id="roomBookingCal" style="margin-bottom: 20px">
                        </div>
                        % if numRooms == 0 and ofMyRooms:
                            <div class="infoMessage" style="margin:40px  0 auto; width: 700px">
                                ${_("You are not responsible for any rooms")}
                            </div>
                        % endif
                        </div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<!--  Container for popup content -->
<div style="display:none;">
    <div id='booking-dialog'>
        <div id="booking-dialog-content" class="dialog-content"></div>
    </div>
</div>

<script type="text/javascript">
% if numRooms != 0 or not ofMyRooms:

    var roomBookingCalendar = new RoomBookingCalendar(
      ${jsonEncode(barsFossil)},
      ${jsonEncode(dayAttrs)},
      ${str(dayLimit).lower()},
      ${str(overload).lower()},
      {"prevURL": "${prevURL}",
       "nextURL": "${nextURL}",
       "formUrl": "${calendarFormUrl}",
       "startD": "${startD}",
       "endD": "${endD}",
       "periodName": "${periodName}",
       "search": ${jsonEncode(search)},
       "params": ${jsonEncode(calendarParams)},
       "newBooking": ${str(newBooking).lower()}
      },
      ${str(manyRooms).lower()},
      '${repeatability}',
      '${str(finishDate).lower()}',
      '${flexibleDatesRange}'
      ${',"' + str(urlHandlers.UHRoomBookingRejectAllConflicting.getURL()) + '"' if showRejectAllButton else ''}
    );
    $E("roomBookingCal").set(roomBookingCalendar.draw());
    roomBookingCalendar.addRepeatabilityBarsHovers();
% endif
</script>
