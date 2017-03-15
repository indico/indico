<%page args="room=None, endpoints=None, event=None, allow_room_change=True, clone_booking=None"/>
<table>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _('Name') }
        </td>
        <td align="left" class="blacktext">
            % if allow_room_change:
                <select name="roomName" id="roomName" class="js-go-to-room" style="width:220px"
                    % if clone_booking:
                        data-clone-booking="${ clone_booking.id | n,j }"
                    % endif
                    >
                    % for roomItem in rooms:
                        <% selected = '' %>
                        % if room.id == roomItem.id:
                            <% selected = 'selected' %>
                        % endif
                        <option data-location="${ roomItem.location_name }" data-id="${ roomItem.id }" ${ selected } class="${ roomItem.kind }">
                            ${ roomItem.location_name + ": " + roomItem.full_name }
                        </option>
                    % endfor
                </select>
                <a target="_blank" href="${ url_for(endpoints['room_details'], event, room) }">${ _('Full details') }</a>
            % else:
                <a href="${ url_for(endpoints['room_details'], event, room) }">
                    ${ room.full_name }
                </a>
            % endif
        </td>
    </tr>

    % if room.photo_id is not None:
        <tr>
            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                ${ _('Interior') }
            </td>
            <td align="left" class="thumbnail">
                <a href="${ room.large_photo_url }" class="js-lightbox">
                    <img border="1" src="${ room.small_photo_url }" alt="${ _('Room picture') }"/>
                </a>
            </td>
        </tr>
    % endif

    % if room.capacity:
        <tr>
            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                ${ _('Capacity') }
            </td>
            <td align="left" class="blacktext">
                ${ room.capacity }&nbsp;${ _('seats') }
            </td>
        </tr>
    % endif

    % if room.key_location:
        <tr>
            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                ${ _('Room key') }
            </td>
            <td align="left" class="blacktext">
                ${ room.key_location }${ inlineContextHelp(_('How to obtain a key. Typically a phone number.')) }
            </td>
        </tr>
    % endif

    % if room.comments:
        <tr>
            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                ${ _('Comments') }
            </td>
            <td align="left" class="blacktext">
                ${ room.comments }
            </td>
        </tr>
    % endif
</table>

% if room.has_vc:
    <div class="warning-message-box new-booking-message-box" style="margin-top: 2em;">
        <div class="message-text ">
            <p>
                ${ _("This room is equipped for videoconferencing.") }
            </p>
            ${ _("If you need this equipment, <strong>do not forget</strong> to select it. If you don't need any of this equipment please <strong>choose another room</strong> unless there is no suitable one available for your meeting.") }
        </div>
    </div>
% endif

<script>
    $(function() {
        $('select.js-go-to-room').on('change', function() {
            var option = $('#roomName option:selected');
            var roomLocation = option.data('location');
            var roomId = option.data('id');

            // cloneBooking will contain the booking id if we are in the 'clone' page
            go_to_room(roomLocation, roomId, $('#roomName').data('cloneBooking'));
        });
    });
</script>
