                              <!-- ROOM -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> <%= _("Room")%></span></td>
                                <td>
                                    <table width="100%">
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Name")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><a href="<%= roomDetailsUH.getURL( room ) %>"><%= room.building %>-<%= room.floor %>-<%= room.roomNr %>
                                                <% if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.roomNr): %>
                                                    <small>(<%= room.name %>)</small>
                                                 <% end %></a>
                                            </td>
                                        </tr>
                                        <% if room.photoId != None: %>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Interior")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="thumbnail">
                                                <a href="<%= room.getPhotoURL() %>" rel="lightbox" title="<%= room.photoId %>">
                                                    <img border="1px" src="<%= room.getSmallPhotoURL() %>" alt="<%= str( room.photoId ) %>"/>
                                                </a>
                                            </td>
                                        </tr>
                                        <% end %>
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> <%= _("Room key")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext"><%= room.whereIsKey %><% contextHelp( 'whereIsKeyHelp' ) %></td>
                                        </tr>
                                    </table>
                                </td>
                              </tr>
