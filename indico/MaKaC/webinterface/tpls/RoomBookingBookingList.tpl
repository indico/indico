    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        <tr>
        <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td>
        </tr>
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">
                            % if not title:
                                <!-- Generic title -->
                                ${ len( reservations ) } ${ _("Booking(s) found")}:
                            % endif
                            % if title:
                                ${ title + " (" + str(len(reservations)) + ")" }:
                            % endif
                            </span>

                            % if prebookingsRejected:
                                <br /><br />
                                <span class="actionSucceeded">${ subtitle }</span>
                                <p style="margin-left: 6px;">${ description }</p>
                            % endif
                            <div style="margin: 12px 0px 16px 0px;" id="roomBookingCal"></div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br />
<<<<<<< HEAD
=======

    <script type="text/javascript">
    var roomBookingCalendar = new RoomBookingCalendar(${ jsonEncode(barsFossil) }, ${ jsonEncode(dayAttrs) }, ${ str(overload).lower() },
            {"prevURL" : "${ prevURL }", "nextURL" : "${ nextURL }", "formUrl" : "${ calendarFormUrl }",
            "startD" : "${ startD }", "endD" : "${ endD }", "periodName" : "${ periodName }",
            "params" : ${ jsonEncode(calendarParams) }}, ${ str(manyRooms).lower() }
            ${',"' + urlHandlers.UHRoomBookingRejectAllConflicting.getURL() + '"' if showRejectAllButton else ''});
    $E("roomBookingCal").set(roomBookingCalendar.draw());
    </script>
