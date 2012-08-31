    <% canModify = block.canModify(user) %>
    <% canDelete = block.canDelete(user) %>
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
                                            <td align="left" class="blacktext">${ formatDate(block.startDate) } &mdash; ${ formatDate(block.endDate) }</td>
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
                                            <td align="left" class="blacktext">${ block.createdByUser.getFullName() }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Date")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ verbose_dt( block.createdDT ) }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Reason")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ block.message }</td>
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
                                        <form style="display:inline;" action="${ urlHandlers.UHRoomBookingBlockingForm.getURL(block) }" method="post">
                                            <input type="submit" class="btn" value="${ _("Modify")}" />
                                        </form>
                                    % endif
                                    % if canDelete:
                                        <form id="deleteBlockingForm" style="display:inline;" action="${ urlHandlers.UHRoomBookingDeleteBlocking.getURL(block) }" method="post">
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
                                        % for principal in block.allowed:
                                            <tr class="blockingHover blockingPadding">
                                                <td>${ principal.getTypeString() }</td>
                                                <td>${ principal.getPrincipal().getFullName() }</td>
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
                                        % for rb in block.blockedRooms:
                                            <tr class="blockingHover blockingPadding">
                                                <td><a href="${ urlHandlers.UHRoomBookingRoomDetails.getURL(rb.room) }">${ rb.room.getFullName() }</a></td>
                                                <td>
                                                    ${ rb.getActiveString() }
                                                    % if rb.active is False:
                                                      by <b>${ rb.rejectedBy }</b>: ${ rb.rejectionReason }
                                                    % elif rb.active is None:
                                                      ${inlineContextHelp(_("This blocking has to be approved by the room owner first."))}
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

 <script type="text/javascript">

 $("#deleteBlocking").click(function(){
     new ConfirmPopup($T("Delete blocking"),$T("Do you really want to DELETE this blocking?"), function(confirmed) {
         if(confirmed) {
             $("#deleteBlockingForm").submit();
         }
     }).open();
     return false;
 });
 </script>