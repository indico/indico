    <% canModify = blocking.can_be_modified(_session.user) %>
    <% canDelete = blocking.can_be_deleted(_session.user) %>
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
                                            <td align="left" class="blacktext">${ blocking.created_by_user.full_name }</td>
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
                                        <a class="i-button" href="${ url_for('rooms.modify_blocking', blocking_id=blocking.id) }">${ _("Modify")}</a>
                                    % endif
                                    % if canDelete:
                                        <input type="button" class="i-button" value="${ _("Delete")}"
                                               data-href="${ url_for('rooms.delete_blocking', blocking_id=blocking.id) }"
                                               data-method="POST"
                                               data-title="${ _('Delete blocking?') }"
                                               data-confirm="${ _('Do you really want to delete this blocking?') }">
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
                                        % for principal in sorted(blocking.allowed, key=lambda x: (x.is_single_person, x.name)):
                                            <tr class="blockingHover blockingPadding">
                                                <td>
                                                    <i class="icon-${'users' if principal.is_group else 'user'}"></i>
                                                    ${ principal.name }
                                                </td>
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
                                                <td><a href="${ url_for('rooms.roomBooking-roomDetails', rb.room) }">${ rb.room.full_name }</a></td>
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
    <br>
