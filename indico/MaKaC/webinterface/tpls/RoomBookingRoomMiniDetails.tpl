<%page args="room=None"/>
    <!-- ROOM -->
    <tr>
        <td>
            <h2 class="group-title">
                ${ _('Room Details') }
            </h2>
        </td>
    </tr>
    <tr>
        <td>
            <table>
                <tr>
                    <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Name') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                        <a href="${ room.details_url }">
                        % if infoBookingMode:
                            <a href="${ room.details_url }">
                            ${ room.building }-${ room.floor }-${ room.number }
                            % if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.number):
                               (${ room.name })
                            % endif
                        % else:
                            <select name="roomName" id="roomName" onchange="isBookable()" style="width:220px">
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
                    <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Interior') }&nbsp;&nbsp;
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
                    <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Capacity') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                        ${ room.capacity }&nbsp;${ _('people') }
                    </td>
                </tr>
                % endif

                % if room.key_location:
                <tr>
                    <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Room key') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                        ${ room.key_location }${ contextHelp('whereIsKeyHelp') }
                    </td>
                </tr>
                % endif

                % if room.comments:
                <tr>
                    <td class="subFieldWidth" align="right" valign="top">
                        ${ _('Comments') }&nbsp;&nbsp;
                    </td>
                    <td align="left" class="blacktext">
                        ${ room.comments }
                    </td>
                </tr>
                % endif
        </table>

        % if room.needs_video_conference_setup:
            <div class="warningMessage" style="text-align: left; max-width: 600px; margin: 3em 1em 1em 1em;">
                ${ _("The conference room you have chosen is equipped for video-conferencing and video-projection. If you need this equipment, <strong>do not forget</strong> to select it. If you don't need any of this equipment please <strong>choose another room</strong>, if a suitable one is free on a suitable location for your meeting. Thank you for your understanding.") }
            </div>
        % endif
    </td>
  </tr>
