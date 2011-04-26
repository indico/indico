<table class="ACtab">
    <tr>
        <td>
            <!-- Guide section -->
            <table style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="2">
                        <p style="padding: 16px 16px 16px 16px;">
                            Booking a room through this interface allows two options:
                        </p>
                            <ul>
                                <li>
                                    <p>Book a room using your name - You may come back later on and assign
                                    the booked room to a particular event.</p>

                                    <form action="${ urlHandlers.UHConfModifRoomBookingSearch4Rooms.getURL( conference, dontAssign = True ) }" method="post">
                                        <div>
                                            <input class="btn" type="submit" value="Book Room"/>
                                        </div>
                                    </form>
                                </li>
                                <li>
                                    <p>Book a room and assign it automatically to the event (data will be automatically
                                    filled in the relative forms).</p>
                                    <p>Select event:</p>
                                    <form action="${ urlHandlers.UHConfModifRoomBookingSearch4Rooms.getURL( conference ) }" method="post">
                                        <ul style="margin-bottom: 20px; list-style-type: none;">
                                            <li><input type="radio" name="event" onclick="this.form.action='${ urlHandlers.UHConfModifRoomBookingSearch4Rooms.getURL( conference ) }';" checked />Lecture: <strong>${escape( conference.getTitle() )}</strong></li>
                                            % for session in conference.getSessionList():
                                                <li><input type="radio" name="event" onclick="this.form.action='${ urlHandlers.UHConfModifRoomBookingSearch4Rooms.getURL( session ) }';" />
                                                     Session:
                                                        <strong>${escape( session.getTitle() )}</strong>
                                                </li>
                                            % endfor
                                            % for contribution in contributions:
                                                <li><input type="radio" name="event" onclick="this.form.action='${ urlHandlers.UHConfModifRoomBookingSearch4Rooms.getURL( contribution ) }';" />
                                                     Contribution:
                                                    <strong>${escape( contribution.getTitle() )}</strong>
                                                </li>
                                            % endfor
                                        </ul>
                                        <div>
                                            <input class="btn" type="submit" value="Book and Assign Room"/>
                                        </div>
                                    </form>

                                </li>
                            </ul>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>


