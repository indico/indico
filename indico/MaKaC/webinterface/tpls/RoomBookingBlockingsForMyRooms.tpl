<h2 class="page-title">
    % if rh.state == 'pending':
      Pending blockings
    % elif rh.state == 'accepted':
      Accepted blockings
    % elif rh.state == 'rejected':
      Rejected blockings
    % else:
      Blockings
    %endif
    for your rooms
</h2>
<br>
% if room_blocks:
    <br>
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
        % for room, roomBlockings in room_blocks.iteritems():
            % for rb in roomBlockings:
                % if lastRoom and lastRoom != room:
                    </tbody>
                    <tbody class="blockingSpacer"><tr><td></td></tr></tbody>
                    <tbody class="blockingForMyRoom">
                % endif
                <tr class="blockingHover" data-id="${ rb.id }">
                    <td>
                        % if lastRoom is not room:
                            <a href="${ url_for('rooms.roomBooking-roomDetails', room) }"><strong>${ room.full_name }</strong></a>
                        % endif
                    </td>
                    <td>${ formatDate(rb.blocking.start_date) }&nbsp;&mdash;&nbsp;${ formatDate(rb.blocking.end_date) }</td>
                    <td><span class="js-state">${ rb.state_name }</span></td>
                    <td>
                      <a href="${ url_for('rooms.blocking_details', blocking_id=str(rb.blocking.id)) }">Details</a>
                      <span class="js-process">
                        % if rb.state == rb.State.pending:
                          [<a href="#" class="processRoomBlocking" data-action="approve">Approve</a>, <a href="#" class="processRoomBlocking" data-action="reject">Reject</a>]
                        % endif
                      </span>
                    </td>
                    <td>${ rb.blocking.reason }</td>
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
            var args = {
                blocked_room_id: rbRow.data('id')
            };

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
                    rbRow.find('.js-process').remove();
                    rbRow.find('.js-state').html(result.state);
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
<a href="${ url_for('rooms.blocking_my_rooms') }" class="${ 'active' if not rh.state else '' }">all states</a> |
<a href="${ url_for('rooms.blocking_my_rooms', state='pending') }" class="${ 'active' if rh.state == 'pending' else '' }">pending</a> |
<a href="${ url_for('rooms.blocking_my_rooms', state='accepted') }" class="${ 'active' if rh.state == 'accepted' else '' }">active</a> |
<a href="${ url_for('rooms.blocking_my_rooms', state='rejected') }" class="${ 'active' if rh.state == 'rejected' else '' }">rejected</a>
