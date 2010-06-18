<% declareTemplate(newTemplateStyle=True) %>
    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">
        <div id="nameCH" class="tip">
             <%= _("""If you live it blank, system will auto generate "building-floor-room" name.""")%> <br />
        </div>
        <div id="siteCH" class="tip">
            <b> <%= _("Required.")%></b>
        </div>
        <div id="buildingCH" class="tip">
            <b> <%= _("Required.")%></b>  <%= _("Must be a positive number.")%><br />
        </div>
        <div id="floorCH" class="tip">
            <b> <%= _("Required.")%></b>
        </div>
        <div id="roomCH" class="tip">
            <b> <%= _("Required.")%></b>  <%= _("Room number.")%>
        </div>
        <div id="isActiveCH" class="tip">
             <%= _("Whether the room exists. Turn it off if room is no longer suitable for meetings, but for some reason you don't want to delete it.")%>
        </div>
        <div id="isReservableCH" class="tip">
             <%= _("Whether the room is bookable by anyone having Indico or NICE account.")%>
        </div>
        <div id="resvsNeedConfirmationCH" class="tip">
             <%= _("Whether bookings must be accepted by person responsible.")%>
        </div>
        <div id="whereIsKeyCH" class="tip">
             <%= _("How to obtain a key. Typically a phone number.")%>
        </div>

        <div id="responsibleCH" class="tip">
            <b> <%= _("Required.")%></b>  <%= _("Person who is responsible for the room.")%> <br />
             <%= _("This person will receive notifications and is able to reject bookings.")%>
        </div>
        <div id="telephoneCH" class="tip">
             <%= _("Room's telephone.")%>
        </div>
        <div id="capacityCH" class="tip">
            <b> <%= _("Required.")%></b>  <%= _("Must be a positive number.")%>
        </div>
        <div id="departmentCH" class="tip">
            ??!
        </div>
        <div id="surfaceCH" class="tip">
            <b> <%= _("Required.")%></b>  <%= _("Surface in square meters. Must be a positive number.")%>
        </div>
        <div id="commentsCH" class="tip">
             <%= _("Any other comments - recommended.")%>
        </div>
        <div id="photoCH" class="tip">
            <b> <%= _("WARNING - PLEASE READ.")%></b><br />
            <ul>
                <li> <%= _("Either you upload two photos (large and small) or none.")%></li>
                <li> <%= _("Small photo must be 90x60 pixels.")%></li>
                <li> <%= _("Large photo may be of any size.")%></li>
            </ul>
        </div>
    </div>
    <!-- END OF CONTEXT HELP DIVS -->

    <form action="<%= urlHandlers.UHRoomBookingSaveRoom.getURL( None ) %>" method="post" enctype="multipart/form-data">
                <table width="95%%" cellpadding="0" cellspacing="0" border="0" align="center">
                    <tr><td class="formTitle"><a href="<%=urlHandlers.UHRoomBookingAdminLocation.getURL(Location.parse(room.locationName))%>">&lt;&lt;Back</a></td></tr>
                    <tr>
                        <td>
                            <span class="formTitle" style="border-bottom-width: 0px">
                            <% if insert: %>
                                 <%= _("New Room")%>
                            <% end %>
                            <% if not insert: %>
                                 <%= _("Modify Room")%>
                                <input type="hidden" name="roomID" id="roomID" value="<%=room.id%>" />
                            <% end %>
                            <input type="hidden" name="roomLocation" id="roomLocation" value="<%=room.locationName%>" />
                            </span>
                            <br />
                            <% if showErrors: %>
                                <br /><span style="color: Red; margin-left: 6px;">Saving failed. There is/are <%= len( errors ) %> error(s):</span>
                                <ul>
                                <% for error in errors: %>
                                    <li><%= error %></li>
                                <% end %>
                                </ul>
                            <% end %>
                            <br /><br />
                            <table width="90%%" align="center" border="0">
                              <!-- LOCATION -->
                              <tr>
                                <td width="24%%" class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Location")%></span></td>
                                <td width="76%%">
                                    <table width="100%%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Location")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <%= room.locationName %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="name" name="name" value="<%= verbose( room.name ) %>" /><% contextHelp( 'nameCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Site")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="site" name="site" value="<%= verbose( room.site ) %>" /><% contextHelp( 'siteCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Building")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="building" name="building" value="<%= verbose( room.building ) %>" /><% contextHelp( 'buildingCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Floor")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="floor" name="floor" value="<%= verbose( room.floor ) %>" /><% contextHelp( 'floorCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Room")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="roomNr" name="roomNr" value="<%= verbose( room.roomNr ) %>" /><% contextHelp( 'roomCH' ) %></td>
                                        </tr>
                                 </table>
                                </td>
                                <td>&nbsp;</td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- OPTIONS -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Options")%></span></td>
                                <td colspan="2">
                                    <table>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Active")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="checkbox" <% if room.isActive: %> checked="checked" <% end %> id="isActive" name="isActive"/> <% contextHelp( 'isActiveCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Public")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="checkbox" <% if room.isReservable: %> checked="checked" <% end %> id="isReservable" name="isReservable" /> <% contextHelp( 'isReservableCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Confirmations")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="checkbox" <% if room.resvsNeedConfirmation: %> checked="checked" <% end %> id="resvsNeedConfirmation" name="resvsNeedConfirmation" /> <% contextHelp( 'resvsNeedConfirmationCH' ) %></td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- CONTACT -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Contact")%></span></td>
                                <td colspan="2">
                                    <table>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Responsible")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="hidden" id="responsibleId" name="responsibleId" value="<%= room.responsibleId %>" />
                                                <input type="text" readonly="readonly" id="responsibleName" name="responsibleName" value="<%= responsibleName %>" />
                                                <input type="button" value="<%= _('Search') %>" onclick="searchForUsers();" />
                                                <% contextHelp( 'responsibleCH' ) %>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Where is key?")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="whereIsKey" name="whereIsKey" value="<%= verbose( room.whereIsKey ) %>" /><% contextHelp( 'whereIsKeyCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Telephone")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="telephone" name="telephone" value="<%= verbose( room.telephone ) %>" /><% contextHelp( 'telephoneCH' ) %></td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- PHOTO -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Photo")%></span></td>
                                <td colspan="2">
                                    <table>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Large photo")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="file" id="largePhotoPath" name="largePhotoPath" value="<% verbose( largePhotoPath ) %>" /> <% contextHelp( 'photoCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Small photo")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="file" id="smallPhotoPath" name="smallPhotoPath" value="<%= verbose( smallPhotoPath ) %>" /></td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- INFORMATION -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Information")%></span></td>
                                <td colspan="2">
                                    <table width="100%%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Capacity")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="capacity" name="capacity" value="<%= verbose( room.capacity ) %>" /> people <% contextHelp( 'capacityCH' ) %> </td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Department")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="division" name="division" value="<%= verbose( room.division ) %>" /><% contextHelp( 'departmentCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Surface area")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" id="surfaceArea" name="surfaceArea" value="<%= verbose( room.surfaceArea ) %>" /> m2<% contextHelp( 'surfaceCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Comments")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><textarea cols="40" id="comments" name="comments" ><%=verbose( room.comments )%></textarea><% contextHelp( 'commentsCH' ) %></td>
                                        </tr>
                                        <tr>
                                            <td align="right" valign="top"><small> <%= _("Unavailable booking periods")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <span id="nonBookablePeriods" name="nonBookablePeriods" >
                                                    <table><tbody>
                                                        <% for i in range(0, len(nonBookableDates)): %>
                                                        <tr class="startEndDate">
                                                            <td class="startEndDateEntry"><%= _("from") %>:</td>
                                                            <td><span id="startDateNonBookablePeriod<%= i %>"></span></td>
                                                            <td class="startEndDateEntry"><%= _("to") %>:</td>
                                                            <td><span id="endDateNonBookablePeriod<%= i %>"></span></td>
                                                        </tr>
                                                        <% end %>
                                                    </tbody></table>
                                                </span>
                                            </td>
                                        </tr>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- CUSTOM ATTRIBUTES -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Custom attributes")%></span></td>
                                <td colspan="2">
                                    <table width="100%%">
                                    <% for ca in attrs: %>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small><%=ca['name']%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><input type="text" name="cattr_<%=ca['name']%>" value=<%= quoteattr(verbose( room.customAtts.get( ca['name'] ) )) %> />
                                            <% if ca['name'] == 'notification email' : %>
                                                <% if ca['required'] : %>
                                                    <% inlineContextHelp( '<b>Required.</b> You can specify more than one email address separated by commas, semicolons or whitespaces.' ) %>
                                                <% end %>
                                                <% else : %>
                                                    <% inlineContextHelp( 'You can specify more than one email address separated by commas, semicolons or whitespaces.' ) %>
                                                <% end %>
                                            <% end %>
                                            <% elif ca['required'] : %>
                                                <% inlineContextHelp( '<b>Required.</b>' ) %>
                                            <% end %>
                                            </td>
                                        </tr>
                                    <% end %>
                                 </table>
                                </td>
                              </tr>
                              <tr><td>&nbsp;</td></tr>
                              <!-- EQUIPMENT -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Equipment")%></span></td>
                                <td colspan="2">
                                    <table width="100%%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Room has")%>:&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <% for eq in possibleEquipment: %>
                                                    <input id="<%= "equ_" + eq %>" name="<%= "equ_" + eq %>" type="checkbox" <% if room.hasEquipment( eq ): %> checked="checked" <%%> ><%= eq %></input><br />
                                                    <% if "video conference" in eq.lower(): %>
                                                        <% for vc in room.__class__.vcList: %>
                                                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input id="<%= "vc_" + vc %>" name="<%= "vc_" + vc %>" type="checkbox" <% if vc in room.getAvailableVC(): %> checked="checked" <%%> ><%= vc %></input><br />
                                                        <% end %>
                                                    <% end %>
                                                <% end %>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                              </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Actions")%></span></td>
                                <td colspan="2">
                                    <input style="margin-left: 18px;" type="submit" class="btn" value="<%= _("Save")%>" />
                                </td>
                            </tr>
                        </table>
                    </tr>
                </table>
    </form>

<script type="text/javascript">
    IndicoUI.executeOnLoad(function(){
    <% for i in range(0, len(nonBookableDates)): %>
        <% nbd = nonBookableDates[i] %>
        var startDateNonBookablePeriod<%= i %> = IndicoUI.Widgets.Generic.dateField(false,{id:'startDateNonBookablePeriod<%= i %>', name:'startDateNonBookablePeriod<%= i %>'});
        $E('startDateNonBookablePeriod<%= i %>').set(startDateNonBookablePeriod<%= i %>);
        <% if nbd.getStartDate() is not None: %>
            startDateNonBookablePeriod<%= i %>.set('<%= nbd.getStartDate().strftime("%d/%m/%Y") %>');
        <% end %>


        var endDateNonBookablePeriod<%= i %> = IndicoUI.Widgets.Generic.dateField(false,{id:'endDateNonBookablePeriod<%= i %>', name:'endDateNonBookablePeriod<%= i %>'});
        $E('endDateNonBookablePeriod<%= i %>').set(endDateNonBookablePeriod<%= i %>);
        <% if nbd.getStartDate() is not None: %>
            endDateNonBookablePeriod<%= i %>.set('<%= nbd.getEndDate().strftime("%d/%m/%Y") %>');
        <% end %>
    <% end %>
    });

  function searchForUsers() {

    var popup = new ChooseUsersPopup($T('Select a responsible'),
                                     true,
                                     null, false,
                                     true, null,
                                     true, true,
                                     function(users) {
                                         $E('responsibleName').set(users[0].name);
                                         $E('responsibleId').set(users[0].id);
                                     });

    popup.execute();
  }
</script>
