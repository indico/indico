    <div style="width:80%;">
    <h2 class="page_title">
    % if rh._createNew:
         ${ _("New Blocking")}
    % else:
         ${ _("Modify Blocking")}
    % endif
    </h2>
    % if rh._createNew:
        <em>When blocking rooms nobody but you, the rooms' managers and those users/groups you specify in the "Allowed users" list will be able to create bookings for the specified rooms in the given timeframe.
        You can also block rooms you do not own - however, those blockings have to be approved by the owners of those rooms.</em>
        <br />
    % endif
    </div>

    <form id="blockingForm" action="${ urlHandlers.UHRoomBookingBlockingForm.getURL(block) }" method="post">
    <input type="hidden" name="action" value="save" />
    <input type="hidden" name="allowedUsers" id="allowedUsers" value="" />
    <input type="hidden" name="blockedRooms" id="blockedRooms" value="" />
    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
        </tr>
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            % if errorMessage:
                                <p class="errorMessage">${ _("Saving failed.") }&nbsp;${ errorMessage }</p>
                            % endif
                            <table width="100%" align="left" border="0">
                              <!-- WHEN -->
                              <tr>
                                <td class="titleUpCellTD" valign="top"><span class="titleCellFormat">${ _("Period") }</span></td>
                                <td bgcolor="white" width="100%">
                                    <div id="dateRange"></div>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- REASON -->
                              <tr>
                                <td class="titleUpCellTD" valign="top"><span class="titleCellFormat"> ${ _("Reason")} ${inlineContextHelp(_("<b>Required.</b> The justification for blocking. Will be displayed to users trying to book."))}</span></td>
                                <td bgcolor="white" width="100%">
                                  <textarea rows="3" cols="50" id="reason" name="reason" >${ verbose( block.message ) }</textarea>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- ROOMS -->
                              <tr>
                                <td class="titleUpCellTD" valign="top"><span class="titleCellFormat"> ${ _("Rooms")} ${inlineContextHelp(_("These rooms will be blocked. Note that the room owner will have to confirm the blocking first unless it is owned by you."))}</span></td>
                                <td bgcolor="white" width="100%">
                                  <div id="roomList" class="PeopleListDiv"></div>
                                  <div id="roomChooser"></div>
                                  <div id="roomAddButton"></div>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- ACL -->
                              <tr>
                                <td class="titleUpCellTD" valign="top"><span class="titleCellFormat"> ${ _("Allowed users/groups")} ${inlineContextHelp(_("These users/groups are allowed to book the selected rooms during the blocking. Note that you as the creator of the blocking are always allowed to book them."))}</span></td>
                                <td bgcolor="white" width="100%">
                                  <div id="allowedPrincipals"></div>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- ACTIONS -->
                              <tr>
                                <td colspan="2">
                                  <table style="width: 100%; background-color: rgb(236, 236, 236); border-top: 1px dashed rgb(119, 119, 119);">
                                    <tr>
                                      <td class="titleUpCellTD"></td>
                                      <td>
                                        <input id="submitBlocking" type="submit" class="btn" value="${_('Create the blocking') if rh._createNew else _('Save')}" />
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
    </form>

    <script type="text/javascript">
        $(document).ready(function() {
            $('#dateRange').daterange({
                % if not rh._createNew:
                labels: ['', ''],
                % endif
                allowPast: ${ 'false' if rh._createNew else 'true' },
                disabled: ${ 'false' if rh._createNew else 'true' },
                startDate: '${ block.startDate.day }/${ block.startDate.month }/${ block.startDate.year }',
                endDate: '${ block.endDate.day }/${ block.endDate.month }/${ block.endDate.year }'
            });
        });

        IndicoUI.executeOnLoad(function() {
            var pm = new IndicoUtil.parameterManager();
            var hasRooms = false;

            $E('submitBlocking').observeClick(function(){
                if (!pm.check()) {
                    return false;
                }
                else if(!hasRooms) {
                    new AlertPopup($T("Warning"), $T("Please add at least one room.")).open();
                    return false;
                }
                % if rh._createNew:
                    new ConfirmPopup($T("Create blocking"),$T("Do you want to create the blocking? Please note that the start and end date cannot be changed after creation."), function(confirmed) {
                        if(confirmed) {
                            $("#blockingForm").submit();
                        }
                    }).open();
                    return false;
                % else:
                    return true;
                % endif
            });

            var serializeACL = function() {
                $('#allowedUsers').val(Json.write(principalField.getUsers()));
            }

            var serializeRooms = function() {
                var roomGuids = [];
                enumerate(blockedRoomList.getAll(), function(value, key) {
                    roomGuids.push(key);
                });
                hasRooms = (roomGuids.length > 0);
                $('#blockedRooms').val(Json.write(roomGuids));
            }

            var principalField = new UserListField(
                    'ShortPeopleListDiv', 'PeopleList',
                    ${ fossilize(p.getPrincipal() for p in block.allowed) }, true, null,
                    true, true, null, null,
                    false, false, false, true,
                    function(data, func) {
                        userListNothing(data, func);
                        serializeACL();
                    },
                    userListNothing,
                    function(data, func) {
                        userListNothing(data, func);
                        serializeACL();
                    });
            serializeACL();
            $E('allowedPrincipals').set(principalField.draw());


            var blockedRoomList = new RoomListWidget('PeopleList', function(roomToRemove, setResult) {
                setResult(true);
                blockedRoomList.set(roomToRemove, null);
                serializeRooms();
            }, true);
            var roomSelectedBefore = ${ fossilize(dict((str(br.room.guid), '%s: %s' % (br.room.locationName, br.room.getFullName())) for br in block.blockedRooms )) };
            each (roomSelectedBefore, function(room, guid) {
                blockedRoomList.set(guid, room);
            });
            serializeRooms();
            $E('roomList').set(blockedRoomList.draw());

            var roomChooser = new SelectRemoteWidget('roomBooking.locationsAndRooms.listWithGuids', {isActive: true}, function() {
                $E('roomChooser').set(roomChooser.draw(), addRoomButton);
                // sort by room name. we cannot do it serverside since objects are not ordered
                $('#roomChooser select > option').detach().sort(function(a, b) {
                    return strnatcmp($(a).text().toLowerCase(), $(b).text().toLowerCase());
                }).appendTo($('#roomChooser select'));
            }, null, null, null, false)
            var addRoomButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Room') );
            addRoomButton.observeClick(function(setResult){
                var selectedValue = roomChooser.select.get();
                var roomName = roomChooser.select.dom.options[roomChooser.select.dom.selectedIndex].innerHTML; // horrible..
                blockedRoomList.set(selectedValue, roomName);
                serializeRooms();
            });
            $E('roomAddButton').set();

            pm.add($E('reason'), 'text', false);
        });
    </script>
