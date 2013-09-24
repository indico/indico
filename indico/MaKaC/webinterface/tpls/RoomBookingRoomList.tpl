
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
                            <h2 class="page_title">
                            % if not title:
                                <!-- Generic title -->
                                ${ len( rooms ) }
                                % if len( rooms ) == 1:
                                    ${ _("room found")}
                                %else:
                                    ${ _("rooms found")}
                                % endif
:
                            % endif
                            % if title:
                                ${ title }:
                            % endif
                            </h2>

% if rooms:
<table width="100%" class="filesTab">
<tr>
<td>
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td style="white-space: nowrap;">
                <table class="resvTable">
                    <tr>
                        <td width="15%" class="dataCaptionFormat"> ${ _("Photo")}</td>
                        <td width="20%" class="dataCaptionFormat"> ${ _("Room name")}</td>
                        <td width="15%" class="dataCaptionFormat"> ${ _("Capacity")}</td>
                        <td width="15%" class="dataCaptionFormat"> ${ _("Site")}</td>
                        <td width="65%" class="dataCaptionFormat"> ${ _("Actions")}</td>
                    </tr>
                    <tr>
                        <td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
                    </tr>
                    % for room in rooms:
                        <% myDetails = detailsUH.getURL( room ) %>
                        <% onClickDetails = 'onclick="window.location=\'%s\'"' % myDetails %>
                        <% bookMe = bookingFormUH.getURL( room ) %>
                        <% modifyMe = urlHandlers.UHRoomBookingRoomForm.getURL( room ) %>
                        % if mapAvailable:
                            <% showMeOnMap = urlHandlers.UHRoomBookingMapOfRooms.getURL(roomID=room.id) %>
                        % endif
                        <tr style="height: 60px" id="${ room.id }" class="resvHover">
                            <td ${onClickDetails} >
                                % if room.photoId != None:
                                    <img src="${ room.getSmallPhotoURL() }" />
                                % endif
                            </td>
                            <td ${onClickDetails} >${ room.building }-${ room.floor }-${ room.roomNr }
                                % if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.roomNr):
                                    <small>(${ room.name })</small>
                                % endif
                            </td>
                            <td ${onClickDetails} align = 'center'>${ room.capacity }</td>
                            <td ${onClickDetails} >${ room.site }</td>
                            <td>
                                <a href="${ myDetails }" > ${ _("view")}</a> <br />
                                % if room.canBook( user ):
                                    <a href="${ bookMe }">book</a> <br />
                                % endif
                                % if room.canPrebook( user ) and not room.canBook( user ):
                                    <a href="${ bookMe }"> ${ _("PRE-book")}</a> <br />
                                % endif
                                % if room.canModify( user ):
                                    <a href="${ modifyMe }"> ${ _("modify")}</a> <br />
                                % endif
                                % if mapAvailable:
                                    <a href="${ showMeOnMap }"> ${ _("show on map")}</a> <br />
                                % endif
                            </td>
                        </tr>
                    % endfor

                    <tr>
                        <td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
                    </tr>
                </table>
                &nbsp;
            </td>
        </tr>
    </table>
    <br>
    <!--</form>-->
    <br>
</td>
</tr>
</table>
% else:
<span class="actionFailed">${noResultsMsg}</span>
% endif


                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br />
