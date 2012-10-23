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
                            <span class="formTitle" style="border-bottom-width: 0px">Room</span><br />
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
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Location")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.locationName }</td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.name }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Site")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.site }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Building")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><a href="https://maps.cern.ch/mapsearch/mapsearch.htm?no=[${ room.building }]" title=" ${ _("Show on map")}">${ room.building }</a></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Floor")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.floor }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Room")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.roomNr }</td>
                                        </tr>
                                        % if user.isAdmin():
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Latitude")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.latitude }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Longitude")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.longitude }</td>
                                        </tr>
                                        % endif
                                 </table>
                                </td>
                                <td width="20%" align="right" class="thumbnail">
                                % if room.photoId != None:
                                    <a href="${ room.getPhotoURL() }" rel="lightbox" title="${ room.photoId }">
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
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Responsible")}&nbsp;</small></td>
                                            <% responsible = room.getResponsible() %>
                                            % if responsible:
                                                <% responsibleName = responsible.getFullName() %>
                                            % else:
                                                <% responsibleName = "" %>
                                            % endif
                                            <td align="left" class="blacktext">${ responsibleName }${contextHelp('responsibleHelp' )}</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Where is key?")}&nbsp;&nbsp;</small></td>
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
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Capacity")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.capacity }${" "}${_("people")}</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Department")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ room.division }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Surface area")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                ${ verbose( room.surfaceArea )}
                                                ${" m&sup2; " if room.surfaceArea else ""}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Room tel.")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ verbose( room.telephone ) }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Comments")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">${ linkify( verbose( room.comments ) ) }</td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Unavailable booking periods")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                            % if room.getNonBookableDates():
                                                <ul><li>${ "</li><li>".join(map(lambda x: 'from %s to %s'%(x.getStartDate().strftime('%d/%m/%Y'), x.getEndDate().strftime('%d/%m/%Y')), room.getNonBookableDates() )) }</li></ul>
                                            % endif
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> ${ _("Maximum advance time for bookings")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                ${ (_("%s days") % room.maxAdvanceDays) if room.maxAdvanceDays else _("Not set")}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                % if not room.isReservable:
                                                    <span class="privateRoom"> ${ _("This room is not publically bookable")}</span>
                                                % endif
                                                % if room.isReservable and room.resvsNeedConfirmation:
                                                    <span class="moderatedRoom"> ${ _("Pre-bookings for this room require confirmation")}</span>
                                                % endif
                                                % if room.isReservable and not room.resvsNeedConfirmation:
                                                    <span class="publicRoom"> ${ _("Bookings for this room are automatically accepted")}</span>
                                                % endif
                                                % if room.isReservable and attrs.get( 'Booking Simba List' ):
                                                    <br><span class="privateRoom">Bookings for this room are restricted to members of the ${ attrs.get('Booking Simba List') } listbox</span>
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
                                            <td class="subFieldWidth" align="right" valign="top"><small>${ name }&nbsp;&nbsp;</small></td>
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
                                            <td class="subFieldWidth" align="right" valign="top"><small>${ _("Room has")}:&nbsp;&nbsp;</small></td>
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
                                                        <% el.append( """<small><font color="grey">(%s) </font></small>"""%(", ".join(VCs))) %>
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
                                    <form name="submits" action="${bookingFormUH.getURL( room )}" method="post">
                                        &nbsp;
                                        % if room.canBook( user ):
                                            <input style="margin-left: 18px;" type="submit" class="btn" value="${ _("Book")}" />
                                        % endif
                                        % if room.canPrebook( user ) and not room.canBook( user ):
                                            <input style="margin-left: 18px;" type="submit" class="btn" value="${ _("PRE-Book")}"/>
                                        % endif
                                        % if room.canModify( user ):
                                            <input style="margin-left: 18px;" type="submit" class="btn" value="${ _("Modify")}" onclick="submit_modify(); return false;" />
                                        % endif
                                        % if room.canDelete( user ):
                                            <input style="margin-left: 18px;" type="submit" class="btn" value="${ _("Delete")}" onclick="submit_delete(); return false;" />
                                        % endif
                                        <input style="margin-left: 18px;" type="submit" class="btn" value="Stats" onclick="submit_stats(); return false;" />
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
