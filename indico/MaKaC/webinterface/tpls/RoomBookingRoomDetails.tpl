    <script type="text/javascript">
        function submit_modify()
        {
            var frm = document.forms['submits']
            frm.action = '${ modifyRoomUH.getURL( room ) }'
            frm.submit()
        }
        function submit_stats()
        {
            var frm = document.forms['submits']
            frm.action = '${ roomStatsUH.getURL( room ) }'
            frm.submit()
        }
        function submit_delete()
        {
            if ( confirm(  "${ _('THIS ACTION IS IRREVERSIBLE. Please note that all archival BOOKINGS WILL BE DELETED with the room. Are you sure you want to DELETE the room?')}" ) )
            {
                var frm = document.forms['submits']
                frm.action = '${ deleteRoomUH.getURL( room ) }'
                frm.submit()
            }
        }
    </script>


    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">
        <div id="whereIsKeyHelp" class="tip">
             ${ _("How to obtain a key. Typically a phone number.")}
        </div>
        <div id="responsibleHelp" class="tip">
             ${ _("Person who is responsible for the room.<br />This person is able to reject your bookings.")}
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
                            <span class="formTitle" style="border-bottom-width: 0px">Room ${ room.name }</span><br />
                            % if actionSucceeded:
                                <br />
                                <span class="actionSucceeded"> ${ _("Action succeeded.")}</span>  ${ _("Please review details below.")}<br />
                                <br />
                            % endif
                            % if deletionFailed:
                                <br />
                                <span class="actionFailed"> ${ _("Deletion failed.")}</span>
                                <p class="actionFailed">
                                     ${ _("This room is booked in the future. Please remove all live bookings first. Please note that system never deletes live bookings automatically.")}
                                </p>
                                <br />
                            % endif
                            <br />
                            <table width="96%" align="left" border="0">
                              <!-- LOCATION -->
                              <tr>
                                <td width="24%" class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Location")}</span></td>
                                <td width="76%">
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Location")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.locationName }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Name")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.name }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Site")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.site }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Building")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext"><a href="${show_on_map}" title=" ${_("Show on map")}">${ room.building }</a></td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Floor")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.floor }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Room")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.roomNr }</td>
                                        </tr>
                                        % if user.isAdmin():
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Latitude")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.latitude }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Longitude")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.longitude }</td>
                                        </tr>
                                        % endif
                                 </table>
                                </td>
                                <td width="20%" align="right" class="thumbnail">
                                % if room.photoId != None:
                                    <a href="${ room.getPhotoURL() }" nofollow="lightbox" title="${ room.photoId }">
                                        <img border="1px" height="100" src="${ room.getPhotoURL() }" alt="${ str( room.photoId ) }"/>
                                    </a>
                                % endif
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- CONTACT -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Contact")}</span></td>
                                <td colspan="2">
                                    <table>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Responsible")}&nbsp;</td>
                                            <% responsible = room.getResponsible() %>
                                            % if responsible:
                                                <% responsibleName = responsible.getFullName() %>
                                            % else:
                                                <% responsibleName = "" %>
                                            % endif
                                            <td align="left" class="blacktext">${ responsibleName }${contextHelp('responsibleHelp' )}</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Where is key?")}&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose( room.whereIsKey ) }${contextHelp('whereIsKeyHelp' )}</td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- INFORMATION -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Information")}</span></td>
                                <td colspan="2">
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Capacity")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.capacity }${" "}${_("people")}</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Department")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ room.division }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Surface area")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                ${ verbose( room.surfaceArea )}
                                                ${" m&sup2; " if room.surfaceArea else ""}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Room tel.")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose( room.telephone ) }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Comments")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ linkify( verbose( room.comments ) ) }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Unavailable periods")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                            % if room.getNonBookableDates():
                                                <ul><li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartDate().strftime('%d/%m/%Y'), x.getEndDate().strftime('%d/%m/%Y')), room.getNonBookableDates() )) }</li></ul>
                                            % endif
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Daily availability periods")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                            % if room.getDailyBookablePeriods():
                                                <ul><li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartTime(), x.getEndTime()), room.getDailyBookablePeriods() )) }</li></ul>
                                            % endif
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"> ${ _("Maximum advance time")}&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                ${ (_("%s days") % room.maxAdvanceDays) if room.maxAdvanceDays else _("Not set")}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                % if not room.isReservable:
                                                    <span class="privateRoom"> ${ _("This room is not publicly bookable")}</span>
                                                % elif room.isReservable and room.resvsNeedConfirmation:
                                                    <span class="moderatedRoom"> ${ _("Pre-bookings for this room require confirmation")}</span>
                                                % elif room.isReservable and not room.resvsNeedConfirmation:
                                                    <span class="publicRoom"> ${ _("Bookings for this room are automatically accepted")}</span>
                                                % endif
                                                % if attrs.get('Booking Simba List') :
                                                    <br><span class="privateRoom">${_("Bookings for this room are restricted to members of the <strong>{0}</strong> listbox").format(attrs.get('Booking Simba List'))}</span>
                                                % endif
                                            </td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- CUSTOM ATTRIBUTES -->
                          % if len( attrs ) > 0:
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Custom attributes")}</span></td>
                                <td colspan="2">
                                    <table width="100%">
                                    % for name, value in attrs.iteritems():
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ name }&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">${ verbose( value ) }</td>
                                        </tr>
                                    % endfor
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                          % endif
                              <!-- EQUIPMENT -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Equipment")}</span></td>
                                <td colspan="2">
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top">${ _("Room has")}:&nbsp;&nbsp;</td>
                                            <td align="left" class="blacktext">
                                                <% l = [] %>
                                                % for eq in room.getEquipment():
                                                    <% el = [] %>
                                                    <% el.append(eq) %>
                                                    % if "video conference" in eq.lower():

                                                        <% VCs = room.getAvailableVC() %>
                                                        % if "I don't know" in VCs:
                                                              <% VCs.remove("I don't know") %>
                                                        % endif
                                                        <% el.append( """<font color="grey">(%s) </font>"""%(", ".join(VCs))) %>
                                                    % endif
                                                    <% l.append("".join(el)) %>
                                                % endfor
                                                ${ ", ".join(l) }
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                              </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Actions")}</span></td>
                                <td colspan="2">
                                    <form id="submits" name="submits" action="${bookingFormUH.getURL( room )}" method="post">
                                        <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                                            % if room.canBook( user ):
                                                <li class="button" style="margin-left: 10px" onclick="$('#submits').submit(); return false;">
                                                    <a href="#" onClick="return false;">${ _("Book")}</a>
                                                </li>
                                            % endif
                                            % if room.canPrebook( user ) and not room.canBook( user ):
                                                <li class="button" style="margin-left: 10px" onclick="$('#submits').submit(); return false;">
                                                    <a href="#" onClick="return false;">${ _("PRE-Book")}</a>
                                                </li>
                                            % endif
                                            % if room.canModify( user ):
                                                <li class="button" style="margin-left: 10px" onclick="submit_modify(); return false;">
                                                    <a href="#" onClick="return false;">${ _("Modify")}</a>
                                                </li>
                                                <li style="display: none"></li>
                                            % endif
                                            % if room.canDelete( user ):
                                                <li class="button" style="margin-left: 10px" onclick="submit_delete(); return false;">
                                                    <a href="#" onClick="return false;">${ _("Delete")}</a>
                                                </li>
                                                <li style="display: none"></li>
                                            % endif
                                                <li class="button" style="margin-left: 10px" onclick="submit_stats(); return false;">
                                                    <a href="#" onClick="return false;">${ _("Stats")}</a>
                                                </li>
                                                <li style="display: none"></li>
                                         </ul>
                                    </form>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="3">
                                    <div id="roomBookingCal"></div>
                                </td>

                            </tr>
                        </table>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <script type="text/javascript">
    var roomBookingCalendar = new RoomBookingCalendar(${ jsonEncode(barsFossil) }, ${ jsonEncode(dayAttrs) });
    $E("roomBookingCal").set(roomBookingCalendar.draw());
    </script>
