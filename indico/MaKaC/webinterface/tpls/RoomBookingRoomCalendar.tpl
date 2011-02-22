% if withConflicts:
    <br /><br />
    <span class="formTitle" style="border-bottom-width: 0px">Conflicts</span><br /><br />
    <p style="margin-left: 10px;">
        % if thereAreConflicts:
            <span style="color: Red; font-weight: bold;">${ conflictsNumber }&nbsp;${ _("conflict(s) with other bookings")}</span><br /><br />
            <%include file="RoomBookingConflicts.tpl"/>
        % else:
            <span style="color: Green">
                % if blockConflicts != 'active':
                    ${_('No conflicts with confirmed bookings, press the "${ buttonText }" button to save your booking.')}
                % else:
                    ${_('No conflicts with confirmed bookings.')}
                % endif
            </span>
        % endif
        % if blockConflicts == 'active':
            <br><span style="color: Red; font-weight: bold;">${ _('Your booking conflicts with a blocking.') }</span>
            ${ inlineContextHelp('A blocking prevents all but selected people from booking a room during the blocked timeframe. To see details about the colliding blocking, move your cursor over the red date in the calendar below.') }
            <br /><br />
        % elif blockConflicts == 'pending':
            <br><span style="color: Orange; font-weight: bold;">${ _('Your booking conflicts with a pending blocking. If you book anyway and the blocking is accepted, your booking will be rejected.') }</span><br /><br />
        % endif
    </p>
% endif



<div id="roomBookingCal"></div>
 <script type="text/javascript">
    var roomBookingCalendar = new RoomBookingCalendar(${ jsonEncode(barsFossil) }, ${ jsonEncode(dayAttrs) });
    $E("roomBookingCal").set(roomBookingCalendar.draw());
</script>