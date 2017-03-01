<h2 class="page-title">
    ${"My Blockings" if rh.only_mine else "Blockings"}
</h2>
<br />
% if blockings:
    <br />
    <table class="blockingTable">
        <thead>
        <tr>
          <td class="dataCaptionFormat">${ _("Period")}</td>
          <td class="dataCaptionFormat">${ _("Owner")}</td>
          <td class="dataCaptionFormat">${ _("Rooms")}</td>
          <td class="dataCaptionFormat">${ _("Reason")}</td>
          <td class="dataCaptionFormat">${ _("Actions")}</td>
        </tr>
        </thead>
        <% lastBlock = None %>
        % for block in blockings:
            % if lastBlock:
                <tbody class="blockingSpacer"><tr><td></td></tr></tbody>
            % endif
            <tbody>
            <tr class="blockingHover blockingPadding">
                <td>${ formatDate(block.start_date) }&nbsp;&mdash;&nbsp;${ formatDate(block.end_date) }</td>
                <td>${ block.created_by_user.full_name }</td>
                <td>${ len(block.blocked_rooms) } room${ (len(block.blocked_rooms) != 1 and 's' or '') }</td>
                <td>${ block.reason }</td>
                <td><a href="${ url_for('rooms.blocking_details', blocking_id=str(block.id)) }">Details</a> | <a href="#" class="blockingShowRooms">Show rooms</a></td>
            </tr>
            <tr class="blockingHover blockingRoomList">
                <td colspan="2"></td>
                <td colspan="2">
                    <div>
                        ${ '<br />'.join('<a href="{}">{}</a>'.format(url_for('rooms.roomBooking-roomDetails', br.room), br.room.full_name) for br in block.blocked_rooms) }
                    </div>
                </td>
                <td></td>
            </tr>
            </tbody>
            <% lastBlock = block %>
        % endfor
    </table>

    <script type="text/javascript">
        $('.blockingShowRooms').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var roomList = $this.closest('tr').next('.blockingRoomList');
            var show = roomList.is(':hidden');
            $this.text(show ? $T('Hide rooms') : $T('Show rooms'));
            roomList.toggle(show);
            $this.closest('tbody').toggleClass('hasRoomList', show);
        });
    </script>
% else:
    <br />
    <em>None found.</em>
    <br />
% endif
<br />
Filter blockings by creator:
<a href="${ url_for('rooms.blocking_list', timeframe=rh.timeframe, only_mine=False) }" class="${ ('' if rh.only_mine else 'active') }">all users</a> |
<a href="${ url_for('rooms.blocking_list', timeframe=rh.timeframe, only_mine=True) }" class="${ ('active' if rh.only_mine else '') }">only myself</a>
<br />
Filter blockings by date:
<a href="${ url_for('rooms.blocking_list', only_mine=rh.only_mine, timeframe='recent') }" class="${ ('active' if rh.timeframe == 'recent' else '') }">active and future blockings</a> |
<a href="${ url_for('rooms.blocking_list', only_mine=rh.only_mine, timeframe='year') }" class="${ ('active' if rh.timeframe == 'year' else '') }">all blockings for this year</a> |
<a href="${ url_for('rooms.blocking_list', only_mine=rh.only_mine, timeframe='all') }" class="${ ('active' if rh.timeframe == 'all' else '') }">all blockings</a>
