<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <!-- the href of the following link is intentionally left empty since we just want to switch to GET -->
    <li><span><a href="">${ _('Specify Search Criteria') }</a></span></li>
    <li><span><a href="#" id="js-back-to-period">${ _('Select Available Period') }</a></span></li>
    <li><span class="current">${ _('Confirm Reservation') }</span></li>
</ul>

<script>
    var userId = "rb-user-${ user.getId() }";
</script>

<%include file="ErrorList.tpl" args='errors=errors, msg=_("There are some errors:")'/>

<h2 class="group-title">
    <i class="icon-location"></i>
    ${ _('Room Details') }
</h2>
<%include file="RoomBookingRoomMiniDetails.tpl" args="room=room, event=event, endpoints=endpoints, allow_room_change=False"/>

<h2 class="group-title">
    <i class="icon-calendar"></i>
    ${ _('Booking Time & Date') }
</h2>
% if room.max_advance_days:
    <div class="info-message-box">
        <div class="message-text">
            ${ _('This room can only be booked {0} days in advance'.format(room.max_advance_days)) }
        </div>
    </div>
%endif
<table>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Type")}
        </td>
        <td align="left" class="blacktext" id="typeInfo">
            ${ repeat_msg }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Start date")}
        </td>
        <td align="left" class="blacktext">
            ${ formatDate(start_dt) }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("End date")}
        </td>
        <td align="left" class="blacktext">
            ${ formatDate(end_dt) }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Time")}
        </td>
        <td align="left" class="blacktext">
            ${ formatTime(start_dt) } - ${ formatTime(end_dt) }
        </td>
    </tr>
</table>

<form method="POST" id="bookingForm">
    <input type="hidden" name="step" value="3">
    ${ form.csrf_token() }
    ${ form.start_dt(type='hidden') }
    ${ form.end_dt(type='hidden') }
    ${ form.repeat_frequency(style='display: none') }
    ${ form.repeat_interval(type='hidden') }
    ${ form.room_id(type='hidden') }

    <h2 class="group-title">
        <i class="icon-user"></i>
        ${ _('Usage of the room') }
    </h2>
    <%include file="RoomBookingNewBookingInfoWidget.tpl" args="form=form"/>

    % if list(form.used_equipment) or form.needs_assistance:
        <h2 class="group-title">
            <i class="icon-projector"></i>
            ${ _('Collaboration & Assistance') }
        </h2>
        <%include file="RoomBookingNewBookingCollaborationWidget.tpl" args="form=form"/>
    % endif

    <h2 class="group-title"></h2>
    <%include file="RoomBookingNewBookingConflictsWidget.tpl" args="form=form"/>

    <div>
        % if form.submit_prebook:
            ${ form.submit_prebook(class_='i-button highlight js-submit-booking') }
        % endif
        % if form.submit_book:
            ${ form.submit_book(class_='i-button highlight js-submit-booking') }
        % endif
        % if not form.submit_book and not form.submit_prebook:
            <div class="info-message-box">
                <div class="message-text">
                    ${ _("You don't have the permission to book this room") }
                </div>
            </div>
        % endif
    </div>
</form>
