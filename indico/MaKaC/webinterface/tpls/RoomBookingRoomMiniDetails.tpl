<%page args="room=None, booking_mode=False"/>
<table>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _('Name') }
        </td>
        <td align="left" class="blacktext">
            % if booking_mode:
                <a href="${ room.details_url }">
                    ${ room.getFullName() }
                </a>
            % else:
                <select name="roomName" id="roomName" class="js-go-to-room" style="width:220px">
                    % for roomItem in rooms:
                        <% selected = '' %>
                        % if room.name == roomItem.name:
                            <% selected = 'selected' %>
                        % endif
                        <option data-location="${ roomItem.location.name }" data-id="${ roomItem.id }" ${ selected } class="${ roomClass(roomItem) }">
                            ${ roomItem.location.name + ": " + roomItem.getFullName() }
                        </option>
                    % endfor
                </select>
                <a target="_blank" href="${ room.details_url }">${ _('Full details') }</a>
            % endif
        </td>
    </tr>

    % if room.photo_id is not None:
        <tr>
            <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                ${ _('Interior') }
            </td>
            <td align="left" class="thumbnail">
                <a href="${ room.large_photo_url }" nofollow="lightbox" title="${ room.photo_id }">
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

% if room.needs_video_conference_setup:
    <div class="warning-message-box new-booking-message-box" style="margin-top: 2em;">
        <div class="message-text ">
            <p>
                ${ _("The conference room you have chosen is equipped for video-conferencing and video-projection.") }
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
            go_to_room(roomLocation, roomId);
        });
    });
</script>
