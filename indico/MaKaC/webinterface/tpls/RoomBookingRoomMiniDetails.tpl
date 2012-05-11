<%page args="room=None"/>
                              <!-- ROOM -->
                              <tr>
                                <td>
                                    <div class="groupTitle bookingTitle">${'Room Details'}</div>
                                </td>
                              </tr>
                              <tr>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <select name="roomName" id="roomName" onchange="isBookable()" style="width:200px">
                                                % for roomItem in rooms:
                                                  <% selected = "" %>
                                                  % if room.name == roomItem.name:
                                                    <% selected = 'selected="selected"' %>
                                                  % endif
                                                  <option data-location="${roomItem.locationName}" data-id="${roomItem.id}" ${ selected } class="${roomClass( roomItem )}">${ roomItem.locationName + ": &nbsp; " + roomItem.getFullName() }</option>
                                                % endfor
                                                </select>
                                            </td>
                                        </tr>
                                        % if room.photoId != None:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Interior")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="thumbnail">
                                                <a href="${ room.getPhotoURL() }" rel="lightbox" title="${ room.photoId }">
                                                    <img border="1px" src="${ room.getSmallPhotoURL() }" alt="${ str( room.photoId ) }"/>
                                                </a>
                                            </td>
                                        </tr>
                                        % endif
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Capacity")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.capacity }&nbsp;${_("people")}</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Room key")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.whereIsKey }${contextHelp('whereIsKeyHelp' )}</td>
                                        </tr>
                                        % if room.comments:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Comments")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.comments }</td>
                                        </tr>
                                        % endif
                                    </table>
                                </td>
                              </tr>
