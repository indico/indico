    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">Room</span><br />
                            <br />
                            <table width="96%" align="left" border="0">
                              <!-- LOCATION -->
                              <tr>
                                <td width="24%" class="titleUpCellTD"><span class="titleCellFormat">Location</span></td>
                                <td width="76%">
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small>Location&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.location.name }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small>Name&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.name }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small>Site&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.site }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small>Building&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><a href="https://maps.cern.ch/mapsearch/mapsearch.htm?no=[${ room.building }]" title="Show on map">${ room.building }</a></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small>Floor&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.floor }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small>Room&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.number }</td>
                                        </tr>
                                 </table>
                                </td>
                                <td width="20%" align="right" class="thumbnail">
                                % if room.has_photo:
                                    <a href="${ room.large_photo_url }" nofollow="lightbox" title="${ room.photo_id }">
                                        <img border="1px" height="100" src="${ room.small_photo_url }" alt="${ str( room.photo_id ) }"/>
                                    </a>
                                % endif
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <tr>
                                <td width="24%" class="titleUpCellTD"><span class="titleCellFormat">Stats</span></td>
                                <td width="76%">
<!-- ============== Key Performance Indicators ================= -->
<!-- =========================================================== -->
    <a name="kpi"></a>
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="5" class="groupTitle">Key Performance Indicators</td>
    </tr>
        <tr>
          <td class="titleUpCellTD" style="width: 100px;"><span class="titleCellFormat">Average occupancy</span></td>
          <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
            <table>
            <tr>
          <form action="${ url_for('rooms.roomBooking-roomStats', roomLocation=room.location.name, roomID=room.id) }">
          <td bgcolor="white" valign="top" style="padding-left: 12px;">
            <select name="period" onChange="this.form.submit();">
            % if period=="pastmonth":
              <option value="pastmonth" selected> past 30 days
              <option value="thisyear"> from beginning of this year
            % endif
            % if period=="thisyear":
              <option value="pastmonth"> past 30 days
              <option value="thisyear" selected> from beginning of this year
            % endif
            </select>
          </td>
          </form>
            </tr>
            <tr>
                <td>
                    <span style="background-color: #C9FFC9; font-weight: bold;">
                        ${ '{0:.02f}%'.format(occupancy) }
                    </span>
                    ${inlineContextHelp('Average room occupancy over the selected period during working hours (8H30-17H30, Monday-Friday including holidays).' )}
                </td>
            </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
          <td class="titleUpCellTD" style="width: 100px;"><span class="titleCellFormat">Bookings</span></td>
          <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
            <table>
            <tr>
                <td>Total:</td>
                <td>
                    ${ room.reservations.count() }
                    ${inlineContextHelp('Total number of bookings including archival, cancelled and rejected.' )}
                </td>
            </tr>
            </table>
            <br />
            <table>
                <tr>
                    <td style="width: 70px;"></td>
                    <td style="width: 70px;">Valid</td>
                    <td style="width: 70px;">Cancelled</td>
                    <td style="width: 70px;">Rejected</td>
                </tr>
                <tr>
                    <td>${ _('Active') }</td>
                    <td><span style="background-color: #C9FFC9; font-weight: bold;">${ stats['active']['valid'] }</span></td>
                    <td>${ stats['active']['cancelled'] }</td>
                    <td>${ stats['active']['rejected'] }</td>
                </tr>
                <tr>
                    <td>${ _('Archived') }</td>
                    <td>${ stats['archived']['valid'] }</td>
                    <td>${ stats['archived']['cancelled'] }</td>
                    <td>${ stats['archived']['rejected'] }</td>
                </tr>
                <tr>
                    <td>${ _('Total') }</td>
                    <td>${ stats['active']['valid'] + stats['archived']['valid'] }</td>
                    <td>${ stats['active']['cancelled'] + stats['archived']['cancelled'] }</td>
                    <td>${ stats['active']['rejected'] + stats['archived']['rejected'] }</td>
                </tr>
            </table>
          </td>
        </tr>
   </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
