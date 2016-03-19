<table cellpadding="0" cellspacing="0" border="0" width="80%">
  <tr>
    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
  </tr>
  <tr>
    <td class="bottomvtab" width="100%">
      <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
        <tr>
          <td class="maincell">
            <h2 class="page-title">${ _(' Found {} rooms ').format(len(rooms)) }</h2>
            % if rooms:
              <table width="100%">
                <tr>
                  <td>
                    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
                      <tr>
                        <td style="white-space: nowrap;">
                          <table id="roomResultTable" class="resvTable tablesorter" style="width: 100%">
                            <thead>
                              <tr>
                                <th width="15%" class="dataCaptionFormat">${ _('Photo') }</th>
                                <th width="20%" class="dataCaptionFormat">${ _('Room name') }</th>
                                <th width="15%" class="dataCaptionFormat">${ _('Capacity') }</th>
                                <th width="15%" class="dataCaptionFormat">${ _('Site') }</th>
                                <th width="65%" class="dataCaptionFormat">${ _('Actions') }</th>
                              </tr>
                            </thead>
                            <tbody>
                              % for room in rooms:
                                <% details_url = url_for('rooms.roomBooking-roomDetails', room) %>
                                <% booking_url = url_for('rooms.room_book', room) %>
                                <% modification_url = url_for('rooms_admin.modify_room', room) %>
                                <% on_click_details_url = 'onclick="window.location=\'{}\'"'.format(details_url) %>
                                % if mapAvailable:
                                  <% show_on_map = url_for('rooms.roomBooking-mapOfRooms', roomID=room.id) %>
                                % endif
                                <tr style="height: 60px" id="${ room.id }" class="resvHover">
                                  <td ${ on_click_details_url }>
                                    <img src="${ room.small_photo_url }" />
                                  </td>
                                  <td ${ on_click_details_url }>
                                    ${ room.building }-${ room.floor }-${ room.number }
                                    % if room.has_special_name:
                                      <small>(${ room.name })</small>
                                    % endif
                                  </td>
                                  <td ${ on_click_details_url } align='center'>
                                    ${ room.capacity if room.capacity is not None else _('n/a') }
                                  </td>
                                  <td ${ on_click_details_url }>
                                    ${ room.site }
                                  </td>
                                  <td>
                                    <a href="${ details_url }">${ _('view') }</a><br/>
                                    % if room.can_be_booked(user):
                                      <a href="${ booking_url }">${ _('book') }</a><br/>
                                    % elif room.can_be_prebooked(user):
                                      <a href="${ booking_url }">${ _('PRE-book') }</a><br/>
                                    % endif
                                    % if room.can_be_modified(user):
                                      <a href="${ modification_url }"> ${ _('modify') }</a><br/>
                                    % endif
                                    % if mapAvailable:
                                      <a href="${ show_on_map }"> ${ _('show on map') }</a><br/>
                                    % endif
                                  </td>
                                </tr>
                              % endfor
                              <tr>
                                <td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
                              </tr>
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    </table>
                    <br>
                    <!--</form>-->
                    <br>
                  </td>
                </tr>
              </table>
            % else:
              <span class="actionFailed">${ _('There are no rooms with this search criteria') }</span>
            % endif
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<br />
<script>
  $(document).ready(function() {
      $('#roomResultTable').tablesorter({
          cssHeader: '',
          headers: {
              0: {
                sorter: false
              },
              2: {
                  sorter: 'digit',
                  string: 'max'
              },
              4: {
                sorter: false
              }
          }
      });
  });
</script>
