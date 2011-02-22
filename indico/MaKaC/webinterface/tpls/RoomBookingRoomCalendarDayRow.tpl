<%page args="room=None, dayDT=None, bars=None, DAY_WIDTH_PX=None, START_H=None"/>
<%
dateclass = "weekday"
datetooltip = ""
roomBlocked = room.getBlockedDay(dayDT)
if roomBlocked:
    block = roomBlocked.block
if roomBlocked and block.canOverride(currentUser, explicitOnly=True):
    dateclass = "blocked_permitted"
    datetooltip = _('Blocked by %s:\n%s\n\n<b>You are permitted to override the blocking.</b>') % (block.createdByUser.getFullName(), block.message)
elif roomBlocked and roomBlocked.active is True:
    if block.canOverride(currentUser, room):
        dateclass = "blocked_override"
        datetooltip = _('Blocked by %s:\n%s\n\n<b>You own this room or are an administrator and are thus permitted to override the blocking. Please use this privilege with care!</b>') % (block.createdByUser.getFullName(), block.message)
    else:
        dateclass = "blocked"
        datetooltip = _('Blocked by %s:\n%s') % (block.createdByUser.getFullName(), block.message)
elif roomBlocked and roomBlocked.active is None:
    dateclass = "preblocked"
    datetooltip = _('Blocking requested by %s:\n%s\n\n<b>If this blocking is approved, any colliding bookings will be rejected!</b>') % (block.createdByUser.getFullName(), block.message)
elif dayDT.weekday() in (5, 6):
    dateclass = "weekend"

if not datetooltip and room.isNonBookableDay(dayDT):
    datetooltip = _('This room cannot be booked for this date due to maintenance reasons')

if datetooltip:
    datetooltip = """onmouseover="domTT_activate(this, event, 'content', '%s', 'delay', 100, 'maxWidth', 320, 'styleClass', 'tip' );" """ % escapeAttrVal(datetooltip.replace('"', '&quot;').replace('\n', '<br>'))
%>

<tr>
    <!-- Date Column -->
    <td>
        % if room.isNonBookableDay(dayDT):
            <span class="unavailable" ${ datetooltip }>
                ${ formatDate(dayDT) }
            </span>
        % else:
            <a href="${ urlHandlers.UHRoomBookingBookingForm.getURL( room )}&day=${ dayDT.day }&month=${ dayDT.month }&year=${ dayDT.year }&ignoreSession=1" class="dateLink ${ dateclass }" ${ datetooltip }>
                <span>
                    ${ formatDate(dayDT) }
                </span>
            </a>
        % endif
    </td>

    <!-- Bars Column -->
    <td>
        <div id="dayDiv_${ dayDT }" class="dayDiv">

            <!-- Render each bar... -->
            % for bar in bars:
                <%include file="RoomBookingRoomCalendarBar.tpl" args="bar = bar, DAY_WIDTH_PX = DAY_WIDTH_PX, START_H = START_H, dayDT = dayDT "/>
            % endfor

            <!-- Render each even hour ( 8, 10, 12, 14 o'clock... ) -->
            % for h in xrange( START_H, 25, 2 ):
                <div id="${ "barDivH_" + str( dayDT ) + "_" + str( h ) }" class="calHour" style="left: ${ int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) }px">${ "%.2d" % h }</div>
            % endfor

        </div>
    </td>
</tr>
