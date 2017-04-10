<% from datetime import datetime %>
<h2 class="page-title">
    % if reservation:
        ${ _('Modify booking') }
    % else:
        ${ _('Book a room') }
    % endif
</h2>

<%include file="ErrorList.tpl" args='errors=form.error_list, msg=_("There are some errors in the data you submitted")'/>

<form id="bookingForm" method="POST" data-only-conflicts="${ int(only_conflicts) }">
    ${ form.csrf_token() }
    <h2 class="group-title">
    <i class="icon-location"></i>
        ${ _('Room details') }
    </h2>
    <%include file="RoomBookingRoomMiniDetails.tpl" args="room=room, event=event, endpoints=endpoints,
                    allow_room_change=not bool(reservation), clone_booking=clone_booking"/>

    % if reservation or form.submit_book or form.submit_prebook:
        <h2 class="group-title">
            <i class="icon-time"></i>
            ${ _('Booking time & date') }
        </h2>
        <%include file="RoomBookingNewBookingPeriodWidget.tpl"
                  args="form=form, can_override=can_override, min_date=(datetime.now() if reservation else None),
                        date_changed=date_changed, past_date=past_date"/>

        % if calendar:
            <h2 class="group-title">
                <i class="icon-calendar"></i>
                ${ _('Calendar preview') }
            </h2>
            ${ calendar }
        % endif

        <h2 class="group-title">
            <i class="icon-user"></i>
            ${ _('Usage of the room') }
        </h2>
        <%include file="RoomBookingNewBookingInfoWidget.tpl" args="form=form"/>

        % if list(form.used_equipment) or form.needs_assistance:
            <h2 class="group-title">
                <i class="icon-projector"></i>
                ${ _('Collaboration & assistance') }
            </h2>
            <%include file="RoomBookingNewBookingCollaborationWidget.tpl" args="form=form"/>
        % endif
    % endif

    <h2 class="group-title"></h2>
    <%include file="RoomBookingNewBookingConflictsWidget.tpl" args="form=form, reservation=reservation"/>

    % if form.submit_book or form.submit_prebook or (hasattr(form, 'submit_update') and form.submit_update):
        ${ form.submit_check(**{'class_': 'i-button', 'data-validation': 'check'}) }
    % endif

    % if form.submit_book:
        ${ form.submit_book(class_='i-button highlight js-submit-booking', disabled=only_conflicts) }
    % endif
    % if form.submit_prebook:
        ${ form.submit_prebook(class_='i-button highlight js-submit-booking') }
    % endif
    % if hasattr(form, 'submit_update') and form.submit_update:
        ${ form.submit_update(class_='i-button highlight js-submit-booking') }
    % endif
    % if not reservation and not form.submit_book and not form.submit_prebook:
        <div class="info-message-box">
            <div class="message-text">
                ${ _("You don't have rights to book this room") }
            </div>
        </div>
    % endif
</form>
