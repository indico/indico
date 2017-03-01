<%
    start_date = blocking.start_date if blocking else form.start_date.data
    end_date = blocking.end_date if blocking else form.end_date.data
%>

<div style="width:80%;">
    <h2 class="page-title">
        % if not blocking:
             ${ _("New Blocking")}
        % else:
             ${ _("Modify Blocking")}
        % endif
    </h2>
    % if not blocking:
        <em>${ _("""When blocking rooms nobody but you, the rooms' managers and those users/groups you specify in the "Allowed users" list will be able to create bookings for the specified rooms in the given timeframe.
        You can also block rooms you do not own - however, those blockings have to be approved by the owners of those rooms.""") }</em>
        <br />
    % endif
</div>

<form id="blockingForm" method="post">
    ${ form.csrf_token() }
    ${ form.blocked_rooms() }
    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
        </tr>
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            % if errors:
                                <p class="errorMessage">${ _("Saving failed.") }<br>${ '<br>'.join(errors) }</p>
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
                                        ${ form.reason(rows=3, cols=50) }
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
                                        ${ form.principals() }
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
                                                   <input id="submitBlocking" type="submit" class="btn" value="${_('Create the blocking') if not blocking else _('Save')}" disabled>
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

<script>
    $(document).ready(function() {
        $('#dateRange').daterange({
            % if blocking:
            labels: ['', ''],
            % endif
            fieldNames: ['start_date', 'end_date'],
            allowPast: ${ 'false' if not blocking else 'true' },
            disabled: ${ 'false' if not blocking else 'true' },
            startDate: '${ start_date.day }/${ start_date.month }/${ start_date.year }',
            endDate: '${ end_date.day }/${ end_date.month }/${ end_date.year }'
        });
    });

    IndicoUI.executeOnLoad(function() {
        var pm = new IndicoUtil.parameterManager();
        var hasRooms = false;

        $('#submitBlocking').on('click', function(){
            if (!pm.check()) {
                return false;
            }
            else if(!hasRooms) {
                new AlertPopup($T("Warning"), $T("Please add at least one room.")).open();
                return false;
            }
            % if not blocking:
                new ConfirmPopup($T("Create blocking"), $T("Do you want to create the blocking? Please note that the start and end date cannot be changed after creation."), function(confirmed) {
                    if(confirmed) {
                        $("#blockingForm").submit();
                    }
                }).open();
                return false;
            % else:
                return true;
            % endif
        });

        var serializeRooms = function() {
            var roomGuids = [];
            enumerate(blockedRoomList.getAll(), function(value, key) {
                roomGuids.push(key);
            });
            hasRooms = (roomGuids.length > 0);
            $('#blocked_rooms').val(Json.write(roomGuids));
        };


        var blockedRoomList = new RoomListWidget('user-list', function(roomToRemove, setResult) {
            setResult(true);
            blockedRoomList.set(roomToRemove, null);
            serializeRooms();
        }, true);
        var roomSelectedBefore = JSON.parse($('#blocked_rooms').val());
        $E('roomList').set(blockedRoomList.draw());

        var roomChooser = new SelectRemoteWidget('roomBooking.locationsAndRooms.listWithGuids', {isActive: true}, function() {
            $E('roomChooser').set(roomChooser.draw(), addRoomButton);
            // sort by room name. we cannot do it serverside since objects are not ordered
            $('#roomChooser select > option').detach().sort(function(a, b) {
                return strnatcmp($(a).text().toLowerCase(), $(b).text().toLowerCase());
            }).appendTo($('#roomChooser select'));

            // Preselect default if we have any
            $.each(roomSelectedBefore, function(i, id) {
                var roomName = $('option', roomChooser.select.dom).filter(function() {
                    return this.value == id;
                }).text();
                blockedRoomList.set(id, roomName);
            });
            serializeRooms(); // Shouldn't be necessary but let's stay on the safe side
            $('#submitBlocking').prop('disabled', false);
        }, null, null, null, false);
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
