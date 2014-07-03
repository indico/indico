<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <li><span><a href="${ url_for('rooms.book') }">${ _('Specify Search Criteria') }</a></span></li>
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
<%include file="RoomBookingRoomMiniDetails.tpl" args="room=room, booking_mode=True"/>

<h2 class="group-title">
    <i class="icon-calendar"></i>
    ${ _('Booking Time & Date') }
</h2>
<div class="info-message-box">
    <div class="message-text">
        ${ _('This room can only be booked {0} days in advance'.format(room.max_advance_days)) }
    </div>
</div>
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
    ${ form.start_date(type='hidden') }
    ${ form.end_date(type='hidden') }
    ${ form.repeat_unit(style='display: none') }
    ${ form.repeat_step(type='hidden') }
    ${ form.room_id(type='hidden') }

    <h2 class="group-title">
        <i class="icon-user"></i>
        ${ _('Booked for user') }
    </h2>
    <%include file="RoomBookingNewBookingInfoWidget.tpl" args="form=form"/>

    <h2 class="group-title">
        <i class="icon-projector"></i>
        ${ _('Collaboration & Assistance') }
    </h2>
    <%include file="RoomBookingNewBookingCollaborationWidget.tpl" args="form=form"/>

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
