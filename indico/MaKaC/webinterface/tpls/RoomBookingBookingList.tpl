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
                        <div class="infoMessage" style="margin: 0px auto 20px auto; width: 280px;">${ _('Click an available period to book it')}</div>
                            <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                              <li class="button" >
                                <a href="${ urlHandlers.UHRoomBookingBookRoom.getURL() }" >${ _('Change search criteria')}</a>
                              </li>
                              <li style="display: none"> </li>
                            </ul>
                        % else :
                            <span class="groupTitle bookingTitle" style="float: left; border-bottom-width: 0px; font-weight: bold; padding-top: 0px; margin: 0px;">
                            % if not title:
                                <!-- Generic title -->
                                ${ numResvs } ${ _("Booking(s) found")}:
                            % elif title:
                                ${ title }
                            % endif
                            </span>
                            % if prebookingsRejected:
                                <br /><br />
                                <span class="actionSucceeded">${ subtitle }</span>
                                <p style="margin-left: 6px;">${ description }</p>
                            % endif
                        % endif
                        <div id="roomBookingCal" style="margin-bottom: 20px"></div>
                         % if newBooking:
                            <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                              <li class="button" >
                                <a href="${ urlHandlers.UHRoomBookingBookRoom.getURL() }" >${ _('Change search criteria')}</a>
                              </li>
                              <li style="display: none"> </li>
                            </ul>
                         % endif
                        </div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script type="text/javascript">
var roomBookingCalendar = new RoomBookingCalendar(${ jsonEncode(barsFossil) }, ${ jsonEncode(dayAttrs) }, ${ str(overload).lower() },
        {"prevURL" : "${ prevURL }", "nextURL" : "${ nextURL }", "formUrl" : "${ calendarFormUrl }",
        "startD" : "${ startD }", "endD" : "${ endD }", "periodName" : "${ periodName }", "search" : ${jsonEncode(search)},
        "params" : ${ jsonEncode(calendarParams)}, "newBooking" : ${ str(newBooking).lower()}}, ${ str(manyRooms).lower() }, '${ repeatability }', '${ str(manyDays).lower() }', '${ str(finishDate).lower() }'
        ${',"' + str(urlHandlers.UHRoomBookingRejectAllConflicting.getURL()) + '"' if showRejectAllButton else ''});
$E("roomBookingCal").set(roomBookingCalendar.draw());
roomBookingCalendar.applyManyDaysBookingLook();

</script>
