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
            <label for="assign-event" style="font-weight: normal;">${ event.getVerboseType() }: <strong>${escape( event.getTitle() )}</strong></label>
        </li>
        % for session in sorted(event.getSessionList(), key=lambda s: s.getStartDate()):
            <li>
                <input type="radio" name="assign" value="session-${ session.getId() }" id="assign-session-${ session.getId() }">
                <label for="assign-session-${ session.getId() }" style="font-weight: normal;">Session: <strong>${escape( session.getTitle() )}</strong></label>
            </li>
        % endfor
        % for contribution in sorted((c for c in event.getContributionList() if c.getStartDate()), key=lambda c: c.getStartDate()):
            <li>
                <input type="radio" name="assign" value="contribution-${ contribution.getId() }" id="assign-contribution-${ contribution.getId() }">
                <label for="assign-contribution-${ contribution.getId() }" style="font-weight: normal;">Contribution: <strong>${escape( contribution.getTitle() )}</strong></label>
            </li>
        % endfor
    </ul>
    <div>
        <input class="i-button" type="submit" value="${ _('Book Room') }">
    </div>
</form>
