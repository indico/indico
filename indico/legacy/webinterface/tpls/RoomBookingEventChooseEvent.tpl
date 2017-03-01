<p>
    ${ _('Booking a room through this interface allows two options:') }
</p>
<ul>
    <li>
        ${ _('Book a room using your name - You may come back later on and assign the booked room to a particular event.') }
    </li>
    <li>
        ${ _('Book a room and assign it automatically to the event (Room and Location of the selected event will be automatically set).') }
    </li>
</ul>
<p><strong>Select event:</strong></p>
<form action="${ url_for('event_mgmt.rooms_book', event) }" method="get">
    <ul style="margin-bottom: 20px; list-style-type: none;">
        <li style="margin-bottom: 1em;">
            <input type="radio" name="assign" value="nothing" id="assign-nothing" checked>
            <label for="assign-nothing" style="font-weight: normal;"><strong>${ _('Just book the room without assigning it') }</strong></label>
        </li>
        <li>
            <input type="radio" name="assign" value="event" id="assign-event">
            <label for="assign-event" style="font-weight: normal;">${ event.as_event.type_.title }: <strong>${escape( event.as_event.title )}</strong></label>
        </li>
        % for sess in sessions:
            <li>
                <input type="radio" name="assign" value="session-${ sess.id }" id="assign-session-${ sess.id }">
                <label for="assign-session-${ sess.id }" style="font-weight: normal;">Session: <strong>${escape( sess.title )}</strong></label>
            </li>
        % endfor
        % for contrib in contribs:
            <li>
                <input type="radio" name="assign" value="contribution-${ contrib.id }" id="assign-contribution-${ contrib.id }">
                <label for="assign-contribution-${ contrib.id }" style="font-weight: normal;">Contribution: <strong>${escape( contrib.title )}</strong></label>
            </li>
        % endfor
    </ul>
    <div>
        <input class="i-button" type="submit" value="${ _('Book Room') }">
    </div>
</form>
