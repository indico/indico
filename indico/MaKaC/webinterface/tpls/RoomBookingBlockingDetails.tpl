    <% canModify = blocking.can_be_modified(user) %>
    <% canDelete = blocking.can_be_deleted(user) %>
    <span class="groupTitleNoBorder">Room Blocking</span><br />
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <table width="90%" align="left" border="0">
                              <!-- WHEN -->
                              <tr>
                                <td class="bookingDisplayTitleCell" valign="top" width="24%"><span class="titleCellFormat"> ${ _("When")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small>${ _("Dates")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ formatDate(blocking.start_date) } &mdash; ${ formatDate(blocking.end_date) }</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- CREATED -->
                            <tr>
                                <td class="bookingDisplayTitleCell" valign="top"><span class="titleCellFormat"> ${ _("Created")}</span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("By")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ blocking.created_by_user.getFullName() }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Date")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ formatDateTime(blocking.created_dt) }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Reason")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ blocking.reason }</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- ACTIONS -->
                            % if canModify or canDelete:
                            <tr>
                                <td class="bookingDisplayTitleCell" valign="top"><span class="titleCellFormat"> ${ _("Actions")}</span></td>
                                <td>
                                    % if canModify:
                                        <form style="display:inline;" action="${ url_for('rooms.modify_blocking', blocking_id=blocking.id) }" method="get">
                                            <input type="submit" class="btn" value="${ _("Modify")}" />
                                        </form>
                                    % endif
                                    % if canDelete:
                                        <form id="deleteBlockingForm" style="display:inline;" action="${ url_for('rooms.delete_blocking', blocking_id=blocking.id) }" method="post">
                                            <input type="submit" id="deleteBlocking" class="btn" value="${ _("Delete")}" />
                                        </form>
                                    % endif
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            % endif
                            <!-- ACL -->
                            <tr>
                                <td class="bookingDisplayTitleCell" valign="top"><span class="titleCellFormat"> ${ _("Allowed users/groups")}</span></td>
                                <td>
                                    <table class="blockingTable">
                                        % for principal in blocking.allowed:
                                            <tr class="blockingHover blockingPadding">
                                                <td>${ principal.entity_name }</td>
                                                <td>${ principal.entity.getFullName() }</td>
                                            </tr>
                                        % endfor
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- Rooms -->
                            <tr>
                                <td class="bookingDisplayTitleCell" valign="top"><span class="titleCellFormat"> ${ _("Rooms")}</span></td>
                                <td>
                                    <table class="blockingTable">
                                        <thead>
                                            <tr>
                                                <th>${_("Room")}</th>
                                                <th>${_("State")}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                        % for rb in blocking.blocked_rooms:
                                            <tr class="blockingHover blockingPadding">
                                                <td><a href="${ urlHandlers.UHRoomBookingRoomDetails.getURL(rb.room) }">${ rb.room.getFullName() }</a></td>
                                                <td>
                                                    ${ rb.state_name }
                                                    % if rb.state == rb.State.pending:
                                                      ${inlineContextHelp(_("This blocking has to be approved by the room owner first."))}
                                                    % elif rb.state == rb.State.rejected:
                                                      by <b>${ rb.rejected_by }</b>: ${ rb.rejection_reason }
                                                    % endif
                                                </td>
                                            </tr>
                                        % endfor
                                        </tbody>
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
    <br />

    <script>
        $('#deleteBlocking').on('click', function(e) {
            e.preventDefault();
            new ConfirmPopup($T('Delete blocking'), $T('Do you really want to DELETE this blocking?'), function(confirmed) {
                if (confirmed) {
                    $('#deleteBlockingForm').submit();
                }
            }).open();
        });
    </script>
