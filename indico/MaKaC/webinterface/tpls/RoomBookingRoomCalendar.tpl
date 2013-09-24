% if withConflicts:
    % if thereAreConflicts:
        <span class="errorMessage" style="text-align: left; margin-left:2px; display: inline-block">
            ${ conflictsNumber }&nbsp;${ _("conflict(s) with other bookings")}
           <ul style="color: #777; list-style: none;">
            <!-- Render each conflict... -->
            <% c = 0; ks = bars.keys(); ks.sort()  %>
            % for dt in ks:
                % for roomBars in bars[dt]:
                    % for bar in roomBars.bars:
                        % if bar.type == Bar.CONFLICT:
                            <li>${ formatDate(bar.startDT.date()) } ${ _("from")} ${ bar.startDT.time() } ${ _("to") } ${ bar.endDT.time() }, ${ _("booked for") } ${ bar.forReservation.bookedForName }</li>
                            <% c += 1 %>
                            % if c > 4:
                                <% break %>
                            % endif
                        % endif
                    % endfor
                % endfor
            % endfor
            </ul>
        </span>
    % else:
        <span id="noConflictsMessage" class="successMessage" style="padding-top: 15px; margin-left:2px; display: inline-block">
            ${_('No conflicts with confirmed bookings.')}
        </span>
    % endif
    % if blockConflicts == 'active':
        <br/>
        <span class="errorMessage" style="margin-left:2px; display: inline-block">${ _('Your booking conflicts with a blocking.') }</span>
        ${ inlineContextHelp('A blocking prevents all but selected people from booking a room during the blocked timeframe. To see details about the colliding blocking, move your cursor over the red date in the calendar below.') }
    % elif blockConflicts == 'pending':
        <br/>
        <span class="warningMessage" style="margin-left:2px; display: inline-block">${ _('Your booking conflicts with a pending blocking. If you book anyway and the blocking is accepted, your booking will be rejected.') }</span>
    % endif
% endif

<div id="roomBookingCal"></div>
<script type="text/javascript">
    var roomBookingCalendar = new RoomBookingCalendar(${ jsonEncode(barsFossil) }, ${ jsonEncode(dayAttrs) });
    $E("roomBookingCal").set(roomBookingCalendar.draw());

    $(document).ready(function(){
        if (window.location.hash != "#conflicts") {
            $("#noConflictsMessage").css('display', 'none');
        }
    });

</script>
