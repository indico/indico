<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <div id="whereIsKeyHelp" class="tip">
    ${ _('How to obtain a key. Typically a phone number.') }
  </div>
  <div id="responsibleHelp" class="tip">
    ${ _('Person who is responsible for the room.<br />This person is able to reject your bookings.') }
 </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

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
            <span class="formTitle" style="border-bottom-width: 0px">
              Room ${ room.name }
            </span><br />
            <br />
            <table width="96%" align="left" border="0">
            <!-- LOCATION -->
              <tr>
                <td width="24%" class="titleUpCellTD">
                  <span class="titleCellFormat"> ${ _('Location') }</span></td>
                    <td width="76%">
                      <table width="100%">
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Location') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ room.location_name }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Name') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ room.name }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Site') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ room.site }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Building') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            <a href="${ show_on_map }" title=" ${ _('Show on map') }">
                              ${ room.building }
                            </a>
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Floor') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ room.floor }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Room') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ room.number }
                          </td>
                        </tr>
                        % if user.isAdmin():
                          <tr>
                            <td class="subFieldWidth" align="right" valign="top">
                              ${ _('Latitude') }&nbsp;&nbsp;
                            </td>
                            <td align="left" class="blacktext">
                              ${ room.latitude }
                            </td>
                          </tr>
                          <tr>
                            <td class="subFieldWidth" align="right" valign="top">
                              ${ _('Longitude') }&nbsp;&nbsp;
                            </td>
                            <td align="left" class="blacktext">
                              ${ room.longitude }
                            </td>
                          </tr>
                        % endif
                      </table>
                    </td>
                    <td width="20%" align="right" class="thumbnail">
                      % if room.photo_id:
                        <a href="${ room.large_photo_url }" class="js-lightbox" title="${ _('Room Photo') }">
                          <img border="1px" height="100" src="${ room.small_photo_url }" alt="${ _('Room Photo') }">
                        </a>
                      % endif
                    </td>
                  </tr>
                 <tr><td>&nbsp;</td></tr>
                 <!-- CONTACT -->
                 <tr>
                    <td class="titleUpCellTD">
                      <span class="titleCellFormat"> ${ _('Contact') }</span>
                    </td>
                    <td colspan="2">
                      <table>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Responsible') }&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(owner_name) } ${contextHelp('responsibleHelp' ) }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Where is key?') }&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(room.key_location) } ${ contextHelp('whereIsKeyHelp') }
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                  <tr><td>&nbsp;</td></tr>
                  <!-- INFORMATION -->
                  <tr>
                    <td class="titleUpCellTD">
                      <span class="titleCellFormat">${ _('Information') }</span>
                    </td>
                    <td colspan="2">
                      <table width="100%">
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Capacity') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            % if room.capacity is not None:
                              ${ room.capacity } ${ _('seats') }
                            % else:
                              ${ _('n/a') }
                            % endif
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Department') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(room.division) }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Surface area') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(room.surface_area) }
                            ${" m&sup2; " if room.surface_area else ""}
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Room tel.')}&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ verbose(room.telephone) }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Comments') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ linkify(verbose(room.comments)) }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top"> ${ _("Unavailable periods")}&nbsp;&nbsp;</td>
                          <td align="left" class="blacktext">
                          % if nonbookable_periods:
                            <ul>
                              % for nbp in nonbookable_periods:
                                <li>
                                    ${ _('from {} to {}').format(
                                        nbp.start_dt.strftime('%d/%m/%Y'),
                                        nbp.end_dt.strftime('%d/%m/%Y')
                                    ) }
                                </li>
                              % endfor
                            </ul>
                          % endif
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Daily availability periods') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            % if bookable_hours:
                              <ul>
                                % for bh in bookable_hours:
                                <li>
                                  ${ _('from {0} to {1}').format(
                                    bh.start_time.strftime('%H:%M'),
                                    bh.end_time.strftime('%H:%M')
                                  ) }
                                </li>
                                % endfor
                              </ul>
                            % endif
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            ${ _('Maximum advance time') }&nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            ${ _('{0} days').format(room.max_advance_days) if room.max_advance_days else _('Not set') }
                          </td>
                        </tr>
                        <tr>
                          <td class="subFieldWidth" align="right" valign="top">
                            &nbsp;&nbsp;
                          </td>
                          <td align="left" class="blacktext">
                            % if not room.is_reservable:
                              <span class="privateRoom">
                                ${ _('This room is not publicly bookable') }
                              </span>
                            % elif room.is_reservable and room.reservations_need_confirmation:
                                <span class="moderatedRoom">
                                  ${ _('Pre-bookings for this room require confirmation') }
                                </span>
                            % elif room.is_reservable and not room.reservations_need_confirmation:
                                <span class="publicRoom">
                                  ${ _('Bookings for this room are automatically accepted') }
                                </span>
                            % endif
                            % if attrs.get('allowed-booking-group'):
                              <br>
                              <span class="privateRoom">
                                ${ _('Bookings for this room are restricted to members of the <strong>{0}</strong> group').format(attrs['allowed-booking-group'].value) }
                              </span>
                            % endif
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                    <tr><td>&nbsp;</td></tr>
                    <!-- CUSTOM ATTRIBUTES -->
                    % if attrs:
                      <tr>
                        <td class="titleUpCellTD">
                          <span class="titleCellFormat">${ _('Custom attributes') }</span>
                        </td>
                        <td colspan="2">
                          <table width="100%">
                            % for attr in attrs.itervalues():
                              <tr>
                                <td class="subFieldWidth" align="right" valign="top">
                                  ${ attr.attribute.title }&nbsp;&nbsp;
                                </td>
                                <td align="left" class="blacktext">
                                  ${ attr.value }
                                </td>
                              </tr>
                            % endfor
                          </table>
                        </td>
                      </tr>
                      <tr><td>&nbsp;</td></tr>
                    % endif
                    <!-- EQUIPMENT -->
                      <tr>
                        <td class="titleUpCellTD">
                          <span class="titleCellFormat"> ${ _('Equipment') }</span>
                        </td>
                        <td colspan="2">
                          <table width="100%">
                            <tr>
                              <td class="subFieldWidth" align="right" valign="top">
                                ${ _('Room has') }:&nbsp;&nbsp;
                              </td>
                              <td align="left" class="blacktext">
                                <%
                                from indico.util.struct.iterables import render_nested
                                %>
                                ${ render_nested(sorted(room.available_equipment, key=lambda x: x.name)) }
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr><td>&nbsp;</td></tr>
                      <!-- ACTIONS -->
                      <tr>
                        <td class="titleUpCellTD">
                          <span class="titleCellFormat">${ _('Actions') }</span>
                        </td>
                        <td colspan="2">
                            <div style="float:left; padding-top: 15px;">
                              % if room.can_be_booked(user):
                                <a class="i-button" href="${ url_for(endpoints['room_book'], event, room) }">${ _('Book') }</a>
                              % elif room.can_be_prebooked(user):
                                <a class="i-button" href="${ url_for(endpoints['room_book'], event, room) }">${ _('PRE-Book') }</a>
                              % endif
                              % if room.can_be_modified(user):
                                <a class="i-button" href="${ modify_room_url }">${ _('Modify') }</a>
                              % endif
                              % if room.can_be_deleted(user):
                                <button class="i-button" data-href="${ delete_room_url }" data-method="POST"
                                   data-title="${ _('Delete Room?') }"
                                   data-confirm="${ _('THIS ACTION IS IRREVERSIBLE. Please note that all archived BOOKINGS WILL BE DELETED with the room. Are you sure you want to DELETE the room?') }">
                                    ${ _('Delete') }
                                </button>
                              % endif
                              <a class="i-button" href="${ stats_url }">${ _('Stats') }</a>
                            </div>
                        </td>
                      </tr>
                      <tr>
                        <td colspan="3">
                          <div id="roomBookingCal" style="margin-top: 40px;">
                              ${ calendar }
                          </div>
                    </td>
                  </tr>
                </table>
              </tr>
            </table>
          </td>
        </tr>
</table>
