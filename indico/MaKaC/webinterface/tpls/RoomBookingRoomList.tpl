<table cellpadding="0" cellspacing="0" border="0" width="80%">
  % if standalone:
    <tr>
      <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
    </tr>
  % endif
  <tr>
    <td class="bottomvtab" width="100%">
      <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
        <tr>
          <td class="maincell">
            <h2 class="page_title">${ title }</h2>
            % if rooms:
              <table width="100%" class="filesTab">
                <tr>
                  <td>
                    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
                      <tr>
                        <td style="white-space: nowrap;">
                          <table class="resvTable" style="width: 100%">
                            <tr>
                              <td width="15%" class="dataCaptionFormat">${ _('Photo') }</td>
                              <td width="20%" class="dataCaptionFormat">${ _('Room name') }</td>
                              <td width="15%" class="dataCaptionFormat">${ _('Capacity') }</td>
                              <td width="15%" class="dataCaptionFormat">${ _('Site') }</td>
                              <td width="65%" class="dataCaptionFormat">${ _('Actions') }</td>
                            </tr>
                            <tr>
                              <td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
                            </tr>
                            % for room in rooms:
                              <% details_url = detailsUH.getURL(room) %>
                              <% booking_url = bookingUH.getURL(room) %>
                              <% modification_url = modificationUH.getURL(room) %>
                              <% on_click_details_url = 'onclick="window.location={}"'.format(details_url) %>
                              % if mapAvailable:
                                <% show_on_map = mapUH.getURL(roomID=room.id) %>
                              % endif
                              <tr style="height: 60px" id="${ room.id }" class="resvHover">
                                <td ${ on_click_details_url }>
                                  % if room.has_photo:
                                    <img src="${ room.getSmallPhotoURL() }" />
                                  % endif
                                </td>
                                <td ${ on_click_details_url }>
                                  ${ room.building }-${ room.floor }-${ room.number }
                                  % if room.has_special_name:
                                    <small>(${ room.name })</small>
                                  % endif
                                </td>
                                <td ${ on_click_details_url } align='center'>
                                  ${ room.capacity }
                                </td>
                                <td ${ on_click_details_url }>
                                  ${ room.site }
                                </td>
                                <td>
                                  <a href="${ details_url }">${ _('view') }</a><br/>
                                  % if room.canBeBookedBy(user):
                                    <a href="${ booking_url }">${ _('book') }</a><br/>
                                  % elif room.canBePrebookedBy(user) and not room.canBeBookedBy(user):
                                    <a href="${ booking_url }">${ _('PRE-book') }</a><br/>
                                  % endif
                                  % if room.canBeModifiedBy(user):
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
                          </table>
                          &nbsp;
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
              <span class="actionFailed">${ noResultsMsg }</span>
            % endif
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<br />
