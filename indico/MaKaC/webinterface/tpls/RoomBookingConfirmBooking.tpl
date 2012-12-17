
    <form id="bookingForm" action="${ saveBookingUH.getURL(conf) }" method="post">
    <input type="hidden" id="afterCalPreview" name="afterCalPreview" value="True" />
    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        % if standalone:
            <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
            </tr>
        % endif
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">
                            % if formMode == FormMode.NEW:
                                Confirm ${bookingMessage}ing
                            % endif
                            % if formMode == FormMode.MODIF:
                                Modify ${bookingMessage}ing
                                <input type="hidden" name="resvID" id="resvID" value="${candResv.id}" />
                            % endif
                            </span><br />

                            <br />
                            <table width="100%" align="left" border="0">
                            <tr>
                                   <td class="titleUpCellTD">${bookingMessage}ing</td>
                                 <td><ul>
                                     <li><strong>Start date:</strong> ${ verbose_dt(candResv.startDT) }</li>
                                    <li><strong>End date:</strong> ${ verbose_dt(candResv.endDT) }</li>
                                    <li><strong>Room:</strong> <a href="${ urlHandlers.UHRoomBookingRoomDetails.getURL(candResv.room) }">${ candResv.room.locationName }&nbsp;${ candResv.room.name }</a></li>
                                 </ul></td>
                            </tr>
                               <tr>
                                   <td class="titleUpCellTD"></td>
                                <td><span style="color: red;">This ${bookingMessage}ing collides with the following ${bookingMessageOther}ings:</span>
                                <ul>
                                    % for col in collisions:
                                    <li>${ col.withReservation.bookedForName }, ${ verbose_dt(col.withReservation.startDT) } - ${ verbose_dt(col.withReservation.endDT) }
                                        (<a href="${ urlHandlers.UHRoomBookingBookingDetails.getURL(col.withReservation) }">more info</a>)</li>
                                    % endfor
                                </ul>
                                % if rejectOthers:
                                    <p>Those PRE-Bookings will be automatically rejected. For recurring bookings, only the conflicting days will be rejected.</p>
                                % else:
                                    <p>It is probable that yours will be rejected in their favour.</p>
                                % endif
                                    <strong>Are you sure</strong> you want to <strong>book it anyway</strong>?
                                </td>
                               </tr>

                            <!-- ACTIONS -->
                            <tr>
                                <td class="titleUpCellTD"></td>
                                <td>
                                    <input type="hidden" name="roomID" id="roomID" value="${candResv.room.id}" />
                                    <input type="hidden" name="roomLocation" id="roomLocation" value="${candResv.room.locationName}" />

                                    <input type="hidden" name="conf" value="${conf.getId() if conf else ""}"/>

                                    <input type="hidden" name="forceAddition" value="True" />

                                    <input name="answer" type="submit" class="btn" value="Yes" />
                                    <input name="answer" type="submit" class="btn" value="No"  />
                                </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                </table>

            </td>
        </tr>
    </table>
    </form>
