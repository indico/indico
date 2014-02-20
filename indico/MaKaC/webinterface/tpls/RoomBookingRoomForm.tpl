<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <div id="nameCH" class="tip">
    ${ _('If you live it blank, system will auto generate "building-floor-room" name.') } <br />
  </div>
  <div id="siteCH" class="tip">
    <b> ${ _('Required.') }</b>
  </div>
  <div id="buildingCH" class="tip">
    <b> ${ _('Required.') }</b>  ${ _('Must be a positive number.') }<br />
  </div>
  <div id="floorCH" class="tip">
    <b> ${ _('Required.') }</b>
  </div>
  <div id="roomCH" class="tip">
    <b> ${ _('Required.') }</b>  ${ _('Room number.') }
  </div>
  <div id="latitudeCH" class="tip">
    <b> ${ _('Latitude.') } </b>
  </div>
  <div id="longitudeCH" class="tip">
    <b> ${ _('Longitude.') } </b>
  </div>
  <div id="isActiveCH" class="tip">
    ${ _("Whether the room exists. Turn it off if room is no longer suitable for meetings, but for some reason you don't want to delete it.") }
  </div>
  <div id="isReservableCH" class="tip">
    ${ _("Whether the room is bookable by anyone having a user account.") }
  </div>
  <div id="resvsNeedConfirmationCH" class="tip">
    ${ _("Whether bookings must be accepted by person responsible.") }
  </div>
  <div id="resvStartNotificationCH" class="tip">
    ${ _("Whether to trigger notifications when a booking for the room begins.") }
  </div>
  <div id="resvStartNotificationBeforeCH" class="tip">
    ${ _("Send the start notification X days before an occurence (leave empty to use default)")  }
  </div>
  <div id="resvEndNotificationCH" class="tip">
    ${ _("Whether to trigger notifications when a booking for the room ends.") }
  </div>
  <div id="resvNotificationToResponsibleCH" class="tip">
    ${ _("Send start/end notifications to the room responsible, too.") }
  </div>
  <div id="resvNotificationAssistanceCH" class="tip">
    ${ _("Send notifications asking for assistance with room setup") }
  </div>
  <div id="whereIsKeyCH" class="tip">
    ${ _("How to obtain a key. Typically a phone number.") }
  </div>
  <div id="responsibleCH" class="tip">
    <b> ${ _('Required.') }</b>  ${ _('Person who is responsible for the room.') } <br />
             ${ _('This person will receive notifications and is able to reject bookings.') }
  </div>
  <div id="telephoneCH" class="tip">
    ${ _('Room\'s telephone.') }
  </div>
  <div id="capacityCH" class="tip">
    <b> ${ _('Required.') }</b>  ${ _('Must be a positive number.') }
  </div>
  <div id="departmentCH" class="tip">
    ??!
  </div>
  <div id="surfaceCH" class="tip">
    <b> ${ _('Required.')}</b>  ${ _('Surface in square meters. Must be a positive number.') }
  </div>
  <div id="commentsCH" class="tip">
    ${ _('Any other comments - recommended.') }
  </div>
  <div id="photoCH" class="tip">
    <b> ${ _('WARNING - PLEASE READ.') }</b><br />
    <ul>
      <li> ${ _('Either you upload two photos (large and small) or none.') }</li>
      <li> ${ _('Small photo must be 90x60 pixels.') }</li>
      <li> ${ _('Large photo may be of any size.') }</li>
    </ul>
  </div>
  <div id="dailyBookablePeriodsCH" class="tip">
    ${ _('Time format: \'HH:MM\'') }
  </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<form action="${ urlHandlers.UHRoomBookingSaveRoom.getURL(roomLocation=location.name) if is_new else urlHandlers.UHRoomBookingSaveRoom.getURL(room) }" method="post" enctype="multipart/form-data">
  <table width="95%" cellpadding="0" cellspacing="0" border="0" align="center">
    <tr>
      <td class="formTitle">
        <a href="${ urlHandlers.UHRoomBookingAdminLocation.getURL(location) }">
          &lt;&lt;${ _('Back') }
        </a>
      </td>
    </tr>
    <tr>
      <td>
        <span class="formTitle" style="border-bottom-width: 0px">
          % if is_new:
            ${ _('New Room') }
          % else:
            ${ _('Modify Room') }
            <input type="hidden" name="roomID" id="roomID" value="${ room.id }" />
          % endif
          <input type="hidden" name="roomLocation" id="roomLocation" value="${ location.name }" />
        </span>
        <br />
        % if errors:
          <br />
          <span style="color: Red; margin-left: 6px;">
            ${ _('Saving failed. There is/are {0} error(s)').format(len(errors)) }:
          </span>
          <ul>
            % for error in errors:
              <li>${ error }</li>
            % endfor
          </ul>
        % endif
        <br /><br />
        <table width="90%" align="center" border="0">
          <!-- LOCATION -->
          <tr>
            <td width="24%" class="titleUpCellTD">
              <span class="titleCellFormat"> ${ _('Location') }</span>
          </td>
          <td width="76%">
            <table width="100%">
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _('Location') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  ${ location.name }
                </td>
              </tr>
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                    <small> ${ _('Name') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="name" name="name" value="${ verbose(room.name) }" />${ contextHelp('nameCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _("Site")}&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="site" name="site" value="${ verbose(room.site) }" />${ contextHelp('siteCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Building') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="building" name="building" value="${ verbose(room.building) }" />${ contextHelp('buildingCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Floor') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="floor" name="floor" value="${ verbose(room.floor) }" />${contextHelp('floorCH' ) }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Room') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="number" name="number" value="${ verbose(room.number) }" />${ contextHelp('roomCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _("Latitude") }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="latitude" name="latitude" value="${ verbose(room.latitude) }" />${ contextHelp('latitudeCH' ) }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Longitude')}&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="longitude" name="longitude" value="${ verbose(room.longitude) }" />${ contextHelp('longitudeCH') }
                </td>
              </tr>
            </table>
          </td>
          <td>&nbsp;</td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- OPTIONS -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat"> ${ _('Options')}</span>
          </td>
          <td colspan="2">
            <table>
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _('Active') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.is_active else '' } id="is_active" name="is_active"/> ${ contextHelp('isActiveCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Public') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.is_reservable else '' } id="is_reservable" name="is_reservable" /> ${ contextHelp('isReservableCH' ) }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Confirmations') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.reservations_need_confirmation else '' } id="reservations_need_confirmation" name="reservations_need_confirmation" /> ${ contextHelp('resvsNeedConfirmationCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Assistance') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.notification_for_assistance else '' } id="notification_for_assistance" name="notification_for_assistance" />${ contextHelp( 'resvNotificationAssistanceCH') }
                </td>
              </tr>
              <tr>
                <!-- TODO: update help -->
                <td align="right" valign="top">
                  <small> ${ _('Notification on booking start - X days before') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" style="width: 20px;" maxlength="1" id="notification_for_start" name="notification_for_start" value="${ room.notification_for_start }" /> ${ contextHelp( 'resvStartNotificationBeforeCH' ) }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Notification on booking end') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.notification_for_end else '' } id="notification_for_end" name="notification_for_end" /> ${ contextHelp( 'resvEndNotificationCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Notification to responsible, too') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="checkbox" ${ 'checked' if room.notification_for_responsible else '' } id="notification_for_responsible" name="notification_for_responsible" /> ${ contextHelp( 'resvNotificationToResponsibleCH') }
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- CONTACT -->
        <tr>
          <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Contact")}</span></td>
          <td colspan="2">
            <table>
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _("Responsible") }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="hidden" id="owner_id" name="owner_id" value="${ verbose(room.owner_id) }" />
                  <input type="text" readonly="readonly" id="owner_name" name="owner_name" value="${ verbose(owner_name) }" />
                  <input type="button" value="${ _('Search') }" onclick="searchForUsers();" />
                  ${ contextHelp('responsibleCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Where is key?') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="key_location" name="key_location" value="${ verbose(room.key_location) }" />${ contextHelp('whereIsKeyCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Telephone') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="telephone" name="telephone" value="${ verbose(room.telephone) }" />${ contextHelp('telephoneCH') }</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- PHOTO -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat">${ _('Photo') }</span>
          </td>
          <td colspan="2">
            <table>
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _('Large photo') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="file" id="largePhotoPath" name="largePhotoPath" value="${ verbose(largePhotoPath) }"/> ${ contextHelp('photoCH' ) }</td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Small photo') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="file" id="smallPhotoPath" name="smallPhotoPath" value="${ verbose(smallPhotoPath) }" />
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- INFORMATION -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat"> ${ _('Information') }</span>
          </td>
          <td colspan="2">
            <table width="100%">
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _('Capacity') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="capacity" name="capacity" value="${ verbose(room.capacity) }" /> ${ _('people') } ${ contextHelp('capacityCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Department') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="division" name="division" value="${ verbose(room.division) }" />${ contextHelp('departmentCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Surface area') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="surface_area" name="surface_area" value="${ verbose(room.surface_area) }" /> ${ _('m2') } ${ contextHelp('surfaceCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Comments') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <textarea cols="40" id="comments" name="comments">${ verbose(room.comments) }</textarea>${ contextHelp('commentsCH') }
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Unavailable booking periods') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <table id="nonBookablePeriodsTable">
                  % for nbd in nonBookableDates:
                    <tr class="startEndDate">
                      <td class="startEndDateEntry">${ _('from') }:</td>
                      <td><span id="startDateNonBookablePeriod${ loop.index }"></span></td>
                      <td class="startEndDateEntry">${ _('to') }:</td>
                      <td><span id="endDateNonBookablePeriod${ loop.index }"></span></td>
                      % if loop.first:
                        <td>
                          <span onclick="addNonBookablePeriod()">
                            <a class="fakeLink">${ _('add period') }</a>
                          </span>
                        </td>
                      % endif
                    </tr>
                  % endfor
                  </table>
                  <input type="hidden" id="nonBookablePeriodCounter" name="nonBookablePeriodCounter" value="0" />
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Daily availability periods') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <table id="dailyBookablePeriodsTable">
                  % for dbp in dailyBookablePeriods:
                    <tr class="startEndDate">
                      <td class="startEndDateEntry">${ _('from') }:</td>
                      <td><span id="startTimeDailyBookablePeriod${ loop.index }"></span></td>
                      <td class="startEndDateEntry">${ _('to') }:</td>
                      <td><span id="endTimeDailyBookablePeriod${ loop.index }"></span>
                        % if loop.first:
                          ${ contextHelp('dailyBookablePeriodsCH') }
                          <td>
                            <span onclick="addDailyBookablePeriod()">
                              <a class="fakeLink">${ _('add period') }</a>
                            </span>
                          </td>
                        % endif
                      </td>
                    </tr>
                  % endfor
                  </table>
                  <input type="hidden" id="dailyBookablePeriodCounter" name="dailyBookablePeriodCounter" value="0" />
                </td>
              </tr>
              <tr>
                <td align="right" valign="top">
                  <small> ${ _('Maximum advance time for bookings') }&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                  <input type="text" id="max_advance_days" name="max_advance_days" value="${ verbose(room.max_advance_days) }" size="10"/> ${ _('days') }
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- CUSTOM ATTRIBUTES -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat"> ${ _('Custom attributes') }</span>
          </td>
          <td colspan="2">
            <!-- TODO: Hiding field when there is no one to choose may be better -->
            % if attrs:
              <table width="100%">
              % for ca in attrs:
                <tr>
                  <td class="subFieldWidth" align="right" valign="top">
                    <small>${ ca['name'] }&nbsp;&nbsp;</small>
                  </td>
                  <td align="left" class="blacktext">
                    <input type="text" name="cattr_${ ca['name'] }" value="${ verbose(room.customAtts.get(ca['name'])) }" />
                    % if ca['name'] == 'notification email':
                      % if ca['required'] :
                        ${ inlineContextHelp('<b>Required.</b> You can specify more than one email address separated by commas, semicolons or whitespaces.') }
                      % else :
                        ${ inlineContextHelp('You can specify more than one email address separated by commas, semicolons or whitespaces.') }
                      % endif
                    % elif ca['required'] :
                      ${ inlineContextHelp('<b>Required.</b>') }
                    % endif
                  </td>
                </tr>
              % endfor
              </table>
            % else:
              ${ _('There are no custom attributes to pick.') }
              <a href="${ urlHandlers.UHRoomBookingAdminLocation.getURL(location) }">${ _('You may first add some to location, {0}.').format(location.name) }</a>
            % endif
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- EQUIPMENT -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat">${ _('Equipments') }</span>
          </td>
          <td colspan="2">
            % if possibleEquipments:
            <table width="100%">
              <tr>
                <td class="subFieldWidth" align="right" valign="top">
                  <small> ${ _('Room has') }:&nbsp;&nbsp;</small>
                </td>
                <td align="left" class="blacktext">
                % for eq, is_checked in possibleEquipments.items():
                  <input id="${ 'equ_' + eq }" name="${ 'equ_' + eq }" type="checkbox" ${' checked' if is_checked else ''} >
                    ${ eq }
                  </input>
                  <br />

                  % if False: #"video conference" in eq.lower():
                    % for vc in room.__class__.vcList:
                      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                      <input id="${ 'vc_' + vc }" name="${ 'vc_' + vc }" type="checkbox" ${' checked' if vc in room.getAvailableVC() else ''} >
                        ${ vc }
                      </input>
                      <br />
                    % endfor
                  % endif
                % endfor
                </td>
              </tr>
            </table>
            % else:
              ${ _('There are no equipments to pick.') }
              <a href="${ urlHandlers.UHRoomBookingAdminLocation.getURL(location) }">${ _('You may add some to location, {0}.').format(location.name) }</a>
            % endif
          </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <!-- ACTIONS -->
        <tr>
          <td class="titleUpCellTD">
            <span class="titleCellFormat"> ${ _('Actions') }</span>
          </td>
          <td colspan="2">
            <input style="margin-left: 18px;" type="submit" class="i-button" value="${ _('Save') }" />
          </td>
        </tr>
      </table>
    </tr>
  </table>
</form>

<script type="text/javascript">
    var nonBookablePeriodCounter = ${ len(nonBookableDates) };
    $('#nonBookablePeriodCounter').val(nonBookablePeriodCounter);

    var dailyBookablePeriodCounter = ${ len(dailyBookablePeriods) };
    $('#dailyBookablePeriodCounter').val(dailyBookablePeriodCounter);

    IndicoUI.executeOnLoad(function() {
        % for nbd in nonBookableDates:
            var startDateField = IndicoUI.Widgets.Generic.dateField(
                true,
                {
                    id: 'startDateNonBookablePeriod${ loop.index }',
                    name: 'startDateNonBookablePeriod${ loop.index }'
                }
            );
            var endDateField = IndicoUI.Widgets.Generic.dateField(
                true,
                {
                    id: 'endDateNonBookablePeriod${ loop.index }',
                    name:'endDateNonBookablePeriod${ loop.index }'
                }
            );

            $E('startDateNonBookablePeriod${ loop.index }').set(startDateField);
            $E('endDateNonBookablePeriod${ loop.index }').set(endDateField);

            startDateField.set(
                '${ nbd.start_date.strftime("%d/%m/%Y %H:%M") if nbd.start_date else ""}'
            );
            endDateField.set(
                '${ nbd.end_date.strftime("%d/%m/%Y %H:%M") if nbd.end_date else ""}'
            );
        % endfor

        % for dbp in dailyBookablePeriods:
            var dateStartEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(
                '${ dbp.start_time.strftime("%H:%M") if dbp.start_time else ""}',
                '${ dbp.end_time.strftime("%H:%M") if dbp.end_time else ""}',
                {
                    id: 'startTimeDailyBookablePeriod${ loop.index }',
                    name: 'startTimeDailyBookablePeriod${ loop.index }',
                    style: { width: '50px' }
                },
                {
                    id: 'endTimeDailyBookablePeriod${ loop.index }',
                    name: 'endTimeDailyBookablePeriod${ loop.index }',
                    style: { width: '50px' }
                }
            );
            $E('startTimeDailyBookablePeriod${ loop.index }').set(
                dateStartEndTimeField.startTimeField
            );
            $E('endTimeDailyBookablePeriod${ loop.index }').set(
                dateStartEndTimeField.endTimeField
            );
        % endfor
    });

    function addNonBookablePeriod() {
        $("#nonBookablePeriodsTable tr:last").after(
            '<tr class="startEndDate"> \
              <td class="startEndDateEntry">${ _("from") }:</td> \
              <td><span id="startDateNonBookablePeriod{0}"></span></td> \
              <td class="startEndDateEntry">${ _("to") }:</td> \
              <td><span id="endDateNonBookablePeriod{0}"></span></td> \
            </tr>'.format(nonBookablePeriodCounter)
        );

        $E('startDateNonBookablePeriod' + nonBookablePeriodCounter).set(
            IndicoUI.Widgets.Generic.dateField(
                true,
                {
                    id: 'startDateNonBookablePeriod' + nonBookablePeriodCounter,
                    name:'startDateNonBookablePeriod' + nonBookablePeriodCounter
                }
            )
        );
        $E('endDateNonBookablePeriod' + nonBookablePeriodCounter).set(
            IndicoUI.Widgets.Generic.dateField(
                true,
                {
                    id: 'endDateNonBookablePeriod' + nonBookablePeriodCounter,
                    name:'endDateNonBookablePeriod' + nonBookablePeriodCounter
                }
            )
        );

        nonBookablePeriodCounter = nonBookablePeriodCounter + 1;
        $('#nonBookablePeriodCounter').val(nonBookablePeriodCounter);
    }

    function addDailyBookablePeriod() {
        $('#dailyBookablePeriodsTable tr:last').after(
            '<tr class="startEndDate"> \
              <td class="startEndDateEntry">${ _("from") }:</td> \
              <td><span id="startTimeDailyBookablePeriod{0}"></span></td> \
              <td class="startEndDateEntry">${ _("to") }:</td> \
              <td><span id="endTimeDailyBookablePeriod{0}"></span></td> \
            </tr>'.format(dailyBookablePeriodCounter)
        );

        newDateStartEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(
            '',
            '',
            {
                id: 'startTimeDailyBookablePeriod' + dailyBookablePeriodCounter,
                name: 'startTimeDailyBookablePeriod' + dailyBookablePeriodCounter,
                style: { width: '50px' }
            },
            {
                id: 'endTimeDailyBookablePeriod' + dailyBookablePeriodCounter,
                name: 'endTimeDailyBookablePeriod' + dailyBookablePeriodCounter,
                style: { width: '50px' }
            }
        );

        $E('startTimeDailyBookablePeriod' + dailyBookablePeriodCounter).set(newDateStartEndTimeField.startTimeField
        );
        $E('endTimeDailyBookablePeriod' + dailyBookablePeriodCounter).set(newDateStartEndTimeField.endTimeField
        );

        dailyBookablePeriodCounter = dailyBookablePeriodCounter + 1;
        $('#dailyBookablePeriodCounter').val(dailyBookablePeriodCounter);
    }

    function searchForUsers() {
        new ChooseUsersPopup(
            $T('Select a responsible'),
            true,
            null, false,
            true, null,
            true, true, false,
            function(users) {
                $E('owner_name').set(users[0].name);
                $E('owner_id').set(users[0].id);
        }).execute();
    }
</script>
