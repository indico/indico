<% from MaKaC.rb_location import RoomGUID %>
<h2 class="page_title">
    % if rh.filterState == 'pending':
      Pending blockings
    % elif rh.filterState == 'accepted':
      Accepted blockings
    % elif rh.filterState == 'rejected':
      Rejected blockings
    % else:
      Blockings
    %endif
    for your rooms
</h2>
<br />
% if roomBlocks:
    <br />
    <table class="blockingTable">
        <thead>
            <tr>
              <td class="dataCaptionFormat">${ _("Room")}</td>
              <td class="dataCaptionFormat">${ _("Period")}</td>
              <td class="dataCaptionFormat">${ _("Status")}</td>
              <td class="dataCaptionFormat">${ _("Actions")}</td>
              <td class="dataCaptionFormat">${ _("Reason")}</td>
            </tr>
        </thead>

        <tbody class="blockingForMyRoom">
        <% lastRoom = None %>
        % for guid, roomBlockings in roomBlocks.iteritems():
            <% room = RoomGUID.parse(guid).getRoom() %>
            % for rb in roomBlockings:
                % if lastRoom and lastRoom is not room:
                    </tbody>
                    <tbody class="blockingSpacer"><tr><td></td></tr></tbody>
                    <tbody class="blockingForMyRoom">
                % endif
                <tr class="blockingHover" data-locator=${ quoteattr(rb.getLocator().getJSONForm()) }>
                    <td>
                        % if lastRoom is not room:
                            <a href="${ urlHandlers.UHRoomBookingRoomDetails.getURL(room) }"><strong>${ room.getFullName() }</strong></a>
                        % endif
                    </td>
                    <td>${ formatDate(rb.block.startDate) }&nbsp;&mdash;&nbsp;${ formatDate(rb.block.endDate) }</td>
                    <td><span class="rb-active">${ rb.getActiveString() }</span></td>
                    <td>
                      <a href="${ urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(rb.block) }">Details</a>
                      <span class="rb-process">
                        % if rb.active is None:
                          [<a href="#" class="processRoomBlocking" data-action="approve">Approve</a>, <a href="#" class="processRoomBlocking" data-action="reject">Reject</a>]
                        % endif
                      </span>
                    </td>
                    <td>${ rb.block.message }</td>
                </tr>
                <% lastRoom = room %>
            % endfor
        % endfor
        </tbody>
    </table>

    <script type="text/javascript">
        $('.processRoomBlocking').click(function(e) {
            e.preventDefault();
            var $this = $(this);
            var rbRow = $this.closest('tr');
            var action = $this.data('action'); // approve/reject
            var args = rbRow.data('locator');

            if(action == 'reject') {
                args.reason = prompt('Please enter a rejection reason.');
                if(!args.reason) {
                    return;
                }
            }

            var killProgress = IndicoUI.Dialogs.Util.progress($T('Processing...'));
            indicoRequest('roombooking.blocking.' + action, args, function(result, error) {
                killProgress();
                if (exists(error)) {
                    IndicoUtil.errorReport(error);
                }
                else {
                    rbRow.find('.rb-process').remove();
                    rbRow.find('.rb-active').html(result.active);
                }
            });
        });
    </script>
% else:
    <br />
    <em>None found.</em>
    <br />
% endif
<br />
Filter by state:
<a href="${ urlHandlers.UHRoomBookingBlockingsMyRooms.getURL() }" class="${ 'active' if not rh.filterState else '' }">all states</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingsMyRooms.getURL(filterState='pending') }" class="${ 'active' if rh.filterState == 'pending' else '' }">pending</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingsMyRooms.getURL(filterState='accepted') }" class="${ 'active' if rh.filterState == 'accepted' else '' }">active</a> |
<a href="${ urlHandlers.UHRoomBookingBlockingsMyRooms.getURL(filterState='rejected') }" class="${ 'active' if rh.filterState == 'rejected' else '' }">rejected</a>
