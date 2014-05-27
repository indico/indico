<h2 class="page-title">
    ${ _('Book a room') }
</h2>

% if form.errors:
    <div class="error-message-box">
        <div class="message-text">
            ${ _('There are some errors in the data you submitted') }:
            <ul>
                % for error in form.errors:
                    <li>${ error }</li>
                % endfor
            </ul>
        </div>
    </div>
% endif

<form id="bookingForm" method="POST">
    <h2 class="group-title">
    <i class="icon-location"></i>
        ${ _('Room details') }
    </h2>
    <!-- TODO remove selector -->
    <%include file="RoomBookingRoomMiniDetails.tpl" args="room=room"/>

    % if form.submit_book or form.submit_prebook:
        <h2 class="group-title">
            <i class="icon-time"></i>
            ${ _('Booking time & date') }
        </h2>
        <%include file="RoomBookingNewBookingPeriodWidget.tpl" args="form=form"/>

        % if calendar:
            <h2 class="group-title">
                <i class="icon-calendar"></i>
                ${ _('Calendar preview') }
            </h2>
            ${ calendar }
        % endif

        <h2 class="group-title">
            <i class="icon-user"></i>
            ${ _('Booked for user') }
        </h2>
        <%include file="RoomBookingNewBookingInfoWidget.tpl" args="form=form"/>

        <h2 class="group-title">
            <i class="icon-projector"></i>
            ${ _('Collaboration & assistance') }
        </h2>
        <%include file="RoomBookingNewBookingCollaborationWidget.tpl" args="form=form"/>
    % endif

    <h2 class="group-title"></h2>
    <%include file="RoomBookingNewBookingConflictsWidget.tpl" args="form=form"/>

    % if form.submit_book or form.submit_prebook:
        ${ form.submit_check(**{'class_': 'i-button', 'data-validation': 'check'}) }
    % endif

    % if form.submit_book:
        ${ form.submit_book(class_='i-button highlight') }
    % endif
    % if form.submit_prebook:
        ${ form.submit_prebook(class_='i-button highlight') }
    % endif
    % if not form.submit_book and not form.submit_prebook:
        <div class="info-message-box">
            <div class="message-text">
                ${ _("You don't have rights to book this room") }
            </div>
        </div>
    % endif
</form>
