<table align="center" width="95%">

<tr>
  <td class="formTitle">
    <a href="${ urlHandlers.UHRoomBookingAdmin.getURL() }">
        &lt;&lt;Back
    </a>
  </td>
</tr>
% if actionSucceeded:
<tr>
  <td>
    <div class="successfulAction">
      <span class="actionSucceeded">
        ${ _('Action succeeded.') }
      </span>  ${ _('A new room has been added.') }
    </div>
  </td>
</tr>
% endif
<tr>
  <td>
<!-- ==================== General Options ====================== -->
<!-- =========================================================== -->
    <table style="margin-top: 20px;">
    <tr>
      <td colspan="2" class="groupTitle">
        ${ _('Location data') }
      </td>
    </tr>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">${ _('Name') }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        ${ location.name }
      </td>
    </tr>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">${ _('Available Rooms') }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <p style="margin-bottom: 4px;">
          ${ _('{0} rooms found in this location.').format(len(rooms)) }
        </p>
        % if rooms:
        <form>
          <select id="roomID">
            % for room in rooms:
              <option value="${ room.id }" class="${ roomClass(room) }">
                ${ room.getFullName() }
              </option>
            % endfor
          </select>
          <input class="i-button" type="button" value="Details" id="viewRoom" data-template="details" />
          <input class="i-button" type="button" value="Modify" id="modifyRoom" data-template="modify" />
          <input class="i-button" type="button" value="Delete" id="deleteRoom" data-template="delete" />
        </form>
        % endif

        <form>
          <input class="i-button" type="button" value="New Room" id="createRoom" data-template="modify" />
        </form>
      </td>
    </tr>
    </table>

    <br/>

    <table>
    <tr>
      <td colspan="2" class="groupTitle">
        ${ _('General options') }
      </td>
    </tr>

    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">${ _('Possible equipment') }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        % if keys.supportsAttributeManagement():
          <p style="color: Green;">
            ${ _('This location supports dynamic equipment management.') }
          </p>
          <form action="${ urlHandlers.UHRoomBookingSaveEquipment.getURL(location) }" method="POST">
            <p>
              <input type="text" id="newEquipmentName" name="newEquipmentName" value="" size="28">
              <input type="submit" class="i-button" value="Add">
            </p>
          </form>
          % if possibleEquipments:
            <form action="${ urlHandlers.UHRoomBookingDeleteEquipment.getURL(location) }" method="POST">
              <p>
                <select name="removeEquipmentName" id="removeEquipmentName">
                  % for eq in possibleEquipments:
                    <option value="${ eq }">${ eq }</option>
                  % endfor
                </select>
                <input type="submit" class="i-button" value="Remove">
              </p>
            </form>
          % endif
          <p>${ _('Information') }:</p>
          <ul style="text-align:justify; font-size: smaller;">
            <li>
              ${ _('Use this to define set of possible equipment for room in the active location.') }
            </li>
            <li>
              ${ _('On the room searching form, user will be able to choose equipment from this set.') }
            </li>
            <li>
              ${ _('On new room creation form, you will be able to choose equipment from this set.') }
            </li>
          </ul>
        % else:
          <span style="color: Red;">
            ${ _('This location does not support dynamic equipment management.') }
          </span><br />
        % endif
      </td>
    </tr>
    <tr><td colspan="2"><hr /></td></tr>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">
            ${ _('Custom room attributes') }
        </span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        % if keys.supportsAttributeManagement():
            <p style="color: Green;">
                ${ _('This location supports dynamic attributes management.') }
            </p>
            <form action="${ urlHandlers.UHRoomBookingSaveCustomAttributes.getURL(location) }" method="POST">
              <table>
                <tr>
                    <td style="width: 200px;">
                      <b>${ _('Name') }</b>
                    </td>
                    <td style="width: 70px;">
                      <b>${ _('Required') }</b>
                    </td>
                    <td style="width: 70px;">
                      <b>${ _('Hidden') }</b>
                    </td>
                    <td style="width: 260px;">
                      <b>${ _('Actions') }</b>
                    </td>
                </tr>
                % for attr in attributes:
                  <tr>
                    <td>${ attr.name }</td>
                    <td>
                      <input type="checkbox" name="${ 'cattr_req_' + attr.name }" ${ 'checked' if attr.is_value_required else '' }>
                    </td>
                    <td>
                      <input type="checkbox" name="${ 'cattr_hid_' + attr.name }" ${ 'checked' if attr.is_value_hidden else '' }>
                    </td>
                    <td>
                      <input type="button" class="i-button" value="Remove" onclick="document.location = '${ urlHandlers.UHRoomBookingDeleteCustomAttribute.getURL( location, removeCustomAttributeName=attr.name) }'; return false;" />
                    </td>
                  </tr>
                % endfor
                <tr>
                  <td>
                    <input type="text" name="newCustomAttributeName" id="newCustomAttributeName">
                  </td>
                  <td>
                    <input type="checkbox" name="newCustomAttributeIsRequired" id="newCustomAttributeIsRequired">
                  </td>
                  <td>
                    <input type="checkbox" name="newCustomAttributeIsHidden" id="newCustomAttributeIsHidden">
                  </td>
                  <td>
                    <input type="submit" class="i-button" value="Add new">
                  </td>
                </tr>
                <tr>
                  <td></td>
                  <td></td>
                  <td></td>
                  <td>
                    <input type="submit" class="i-button" value="Save">
                      ${ inlineContextHelp('Updates `required` and `hidden` for all existing attributes.' ) }
                  </td>
                </tr>
              </table>
            </form>
            <p>${ _('Information') }:</p>
            <ul style="text-align:justify; font-size: smaller;">
              <li>
                ${ _('Use this to define room attribues that are specific to the location.') }
              </li>
              <li>
                ${ _('Custom attributes are subject to free-text search. This means that they <b>will</b> work with "Room description must contain" box on a searching form.') }
              </li>
              <li>
                ${ _('Custom attributes does not have type. They are kept as free text. It is impossible to add any kind of validation without coding.') }
              </li>
            </ul>
        % else:
          <span style="color: Red;">
            ${ _('This location does not support dynamic attributes management.') }
          </span><br />
        % endif
      </td>
    </tr>
    <tr><td colspan="2"><hr /></td></tr>
    <tr>
      <td class="titleUpCellTD" style="width: 160px;">
        <span class="titleCellFormat">
          ${ _('Room map attributes') }
        </span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <div id="AspectsListHolder">
        </div>
      </td>
    </tr>

  </table>
  <br>

<script type="text/javascript">

    var urlTemplates = {
        'details': ${ urlHandlers.UHRoomBookingRoomDetails.getURL().js_router | j,n },
        'modify': ${ urlHandlers.UHRoomBookingRoomForm.getURL().js_router | j,n },
        'delete': ${ urlHandlers.UHRoomBookingDeleteRoom.getURL().js_router | j,n }
    };

    $('#viewRoom, #modifyRoom, #createRoom').on('click', function(e) {
        e.preventDefault();
        var args = {
            roomLocation: ${ location.name | j,n }
        };
        if(this.id != 'createRoom') {
            args.roomID = $('#roomID').val();
            if(!args.roomID) {
                return;
            }
        }
        location.href = build_url(urlTemplates[$(this).data('template')], args);
    });

    $('#deleteRoom').on('click', function(e) {
        e.preventDefault();
        if(!$('#roomID').val()) {
            return;
        }
        var url = build_url(urlTemplates[$(this).data('template')], {
            roomLocation: ${ location.name | j,n },
            roomID: $('#roomID').val()
        });
        new ConfirmPopup($T("Delete room"), $T("Are you sure you want to delete this room? All related bookings will also be deleted. this action is PERMANENT!"), function(confirmed) {
            if (confirmed) {
                $('<form>', {
                    method: 'POST',
                    action: url
                }).submit();
            }
        }).open();
    });


var newAspectsHandler = function(newAspect, setResult) {
    var killProgress = IndicoUI.Dialogs.Util.progress();
    indicoRequest(
        'roomBooking.mapaspects.create',
        {
            location: '${ location.name }',
            aspect: newAspect
        },
        function(result, error) {
            killProgress();
            if (!error) {
                setResult({ok: true, id: result});
            } else {
                IndicoUtil.errorReport(error);
                setResult(false);
            }
        }
    );
}

var editAspectHandler = function(oldAspect, setResult, newAspect) {
    var killProgress = IndicoUI.Dialogs.Util.progress();
    indicoRequest(
        'roomBooking.mapaspects.update',
        {
            location: '${ location.name }',
            aspect: newAspect
        },
        function(result, error) {
            killProgress();
            if (!error) {
                setResult(true);
            } else {
                IndicoUtil.errorReport(error);
                setResult(false);
            }
        }
    );
}

var removeAspectHandler = function(aspect, setResult) {
    var killProgress = IndicoUI.Dialogs.Util.progress();
    indicoRequest(
        'roomBooking.mapaspects.remove',
        {
            location: '${ location.name }',
            aspectId: aspect.get('id')
        },
        function(result, error) {
            killProgress();
            if (!error) {
                setResult(true);
            } else {
                IndicoUtil.errorReport(error);
                setResult(false);
            }
        }
    );
}

indicoRequest(
    'roomBooking.mapaspects.list',
    {
        location: '${ location.name }'
    },
    function(result, error) {
        if (!error) {
            var aspectsListField = new MapAspectListField(
                'AspectsListDiv',
                'PeopleList',
                result,
                newAspectsHandler,
                editAspectHandler,
                removeAspectHandler
            );
            $E('AspectsListHolder').set(aspectsListField.draw());
        } else {
            // TODO: remove logs
            console.log(result);
            console.log(error);
            IndicoUtil.errorReport(error);
        }
    }
);

</script>

<!-- ============== Key Performance Indicators ================= -->
<!-- =========================================================== -->
    <a name="kpi"></a>
    <table>
    <tr>
      <td colspan="5" class="groupTitle">
        ${ _('Key Performance Indicators') }
      </td>
    </tr>
    % if not withKPI:
    <tr>
      <td colspan="2" style="padding-left: 30px; padding-top: 30px;">
        <a href="${ urlHandlers.UHRoomBookingAdminLocation.getURL(location, withKPI=True) }">
          ${ _('Show Key Performance Indicators') }
        </a><br />
        ${ _('Computations may take <strong>several minutes</strong>') }.
      </td>
      <br /><br />
    </tr>
    % else:
    <tr>
      <td class="titleUpCellTD" style="width: 100px;">
        <span class="titleCellFormat">${ _('Rooms') }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <table>
          <tr>
            <td style="text-align: right;">${ _('Average occupation') }:</td>
            <td>
              <span style="background-color: #C9FFC9; font-weight: bold;">${ kpiAverageOccupation }</span> ${inlineContextHelp('Average room occupation in last 30 days during working hours (8H30-17H30, Monday-Friday including holidays). Only active, publically reservable rooms are taken into account.' )}
            </td>
          </tr>
          <tr><td>&nbsp;</td></tr>
          <tr>
            <td style="width: 140px; text-align: right;">
              ${ _('Total') }:
            </td>
            <td>
              ${ kpiTotalRooms } ${ inlineContextHelp('Total number of rooms (including deactivated).') }
            </td>
          </tr>
          <tr>
            <td style="text-align: right;">
              ${ _('Active') }:
            </td>
            <td>
              ${ kpiActiveRooms } ${ inlineContextHelp('Total number of active rooms.') }
            </td>
          </tr>
          <tr>
            <td style="text-align: right;">
              ${ _('Reservable') }:
            </td>
            <td>
              ${ kpiReservableRooms } ${ inlineContextHelp('Total number of rooms that are <b>publically</b> reservable. The rest are reservable only by people responsible.') }
            </td>
          </tr>
          <tr><td>&nbsp;</td></tr>
          <tr>
            <td style="text-align: right;">
              ${ _('Reservable capacity') }:
            </td>
            <td>
              ${ kpiReservableCapacity } ${ inlineContextHelp('Total capacity of rooms that are <b>publically</b> reservable.') }
            </td>
          </tr>
          <tr>
            <td style="text-align: right;">
              ${ _('Reservable surface') }:
            </td>
            <td>
              ${ kpiReservableSurface } &sup2; ${ inlineContextHelp('Total surface of rooms that are <b>publically</b> reservable.') }
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
      <td class="titleUpCellTD" style="width: 100px;">
        <span class="titleCellFormat">${ _('Bookings') }</span>
      </td>
      <td bgcolor="white" valign="top" class="blacktext" style="padding-left: 12px;">
        <table>
          <tr>
            <td>${ _('Total') }:</td>
            <td>${ kbiTotalBookings } ${ inlineContextHelp('Total number of bookings including archival, cancelled and rejected.' ) }</td>
          </tr>
        </table>
        <br />
        <table>
          <tr>
            <td style="width: 70px;"></td>
            <td style="width: 70px;">${ _('Valid') }</td>
            <td style="width: 70px;">${ _('Cancelled') }</td>
            <td style="width: 70px;">${ _('Rejected') }</td>
          </tr>
          <tr>
            <td>${ _('Live') }</td>
            <td>
              <span style="background-color: #C9FFC9; font-weight: bold;">
                ${ stats['liveValid'] }
              </span>
            </td>
            <td>${ stats['liveCancelled'] }</td>
            <td>${ stats['liveRejected'] }</td>
          </tr>
          <tr>
            <td>${ _('Archival') }</td>
            <td>${ stats['archivalValid'] }</td>
            <td>${ stats['archivalCancelled'] }</td>
            <td>${ stats['archivalRejected'] }</td>
          </tr>
          <tr>
            <td>${ _('Total') }</td>
            <td>${ stats['liveValid'] + stats['archivalValid'] }</td>
            <td>${ stats['liveCancelled'] + stats['archivalCancelled'] }</td>
            <td>${ stats['liveRejected'] + stats['archivalRejected'] }</td>
          </tr>
        </table>
      </td>
    </tr>
    % endif
  </table>
  <br />
</td>
</tr>
</table>
