<span class="groupTitleNoBorder">${"My Blockings" if rh.onlyMine else "Blockings"}</span>
<br />
% if blocks:
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
        % for block in blocks:
            % if lastBlock:
                <tbody class="blockingSpacer"><tr><td></td></tr></tbody>
            % endif
            <tbody>
            <tr class="blockingHover blockingPadding">
                <td>${ formatDate(block.startDate) }&nbsp;&mdash;&nbsp;${ formatDate(block.endDate) }</td>
                <td>${ block.createdByUser.getFullName() }</td>
                <td>${ len(block.blockedRooms) } room${ (len(block.blockedRooms) != 1 and 's' or '') }</td>
                <td>${ block.message }</td>
                <td><a href="${ urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(block) }">Details</a> | <a href="#" class="blockingShowRooms">Show rooms</a></td>
            </tr>
            <tr class="blockingHover blockingRoomList">
                <td colspan="2"></td>
                <td colspan="2">
                    <div>
                        ${ '<br />'.join('<a href="%s">%s</a>' % (urlHandlers.UHRoomBookingRoomDetails.getURL(br.room), br.room.getFullName()) for br in block.blockedRooms) }
                    </div>
                </td>
                <td></td>
            </tr>
            </tbody>
            <% lastBlock = block %>
        % endfor
    </table>

    <script type="text/javascript">
    (function($) {
        $('.blockingShowRooms').toggle(function(e) {
            e.preventDefault();
            var $this = $(this);
            $this.text('Hide rooms').closest('tr').next('.blockingRoomList').show();
            $this.closest('tbody').addClass('hasRoomList');
        }, function(e) {
            e.preventDefault();
            var $this = $(this);
            $this.text('Show rooms').closest('tr').next('.blockingRoomList').hide();
            $this.closest('tbody').removeClass('hasRoomList');
        });
    })(jQuery);
    </script>
% else:
    <br />
    <em>None found.</em>
    <br />
% endif
<br />
Filter blockings by creator:
<a href="${ urlHandlers.UHRoomBookingBlockingList.getURL(onlyThisYear=rh.onlyThisYear, onlyRecent=rh.onlyRecent) }" class="${ ('' if rh.onlyMine else 'active') }">all users</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingList.getURL(onlyThisYear=rh.onlyThisYear, onlyRecent=rh.onlyRecent, onlyMine=True) }" class="${ ('active' if rh.onlyMine else '') }">only myself</a>
<br />
Filter blockings by date:
<a href="${ urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=rh.onlyMine, onlyThisYear=True, onlyRecent=True) }" class="${ ('active' if rh.onlyRecent else '') }">active and future blockings</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=rh.onlyMine) }" class="${ ('' if not rh.onlyThisYear or rh.onlyRecent else 'active') }">all blockings for this year</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=rh.onlyMine, onlyThisYear=False) }" class="${ ('' if rh.onlyThisYear or rh.onlyRecent else 'active') }">all blockings</a>