
    <table cellpadding="0" cellspacing="0" border="0" width="80%%">
		<% if standalone: %>
		    <tr>
		    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%%">&nbsp;</td> <!-- lastvtabtitle -->
		    </tr>
		<% end %>
        <tr>
            <td class="bottomvtab" width="100%%">
                <table width="100%%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">
                            <% if not title: %>
                                <!-- Generic title -->
                                <%= len( rooms ) %>
                                <% if len( rooms ) == 1: %>
                                    <%= " " + _("room found")%>
                                <%end%>
                                <%else:%>
                                    <%= " " + _("rooms found")%>
                                <%end%>:
                            <% end %>
                            <% if title: %>
                                <%= title %>:
                            <% end %>
                            </span><br /><br />


<table width="100%%" class="filesTab">
<tr>
<td>
	<table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
		<tr>
			<td style="white-space: nowrap;">
                <script type="text/javascript">
                isOver = false
                function handleMouseOverResv( id ) {
	                if ( isOver ) return
	                isOver = true
	                resvTR = document.getElementById( id )
	                resvTR.bgColor = '#f0f0f0'
                }
                function handleMouseOutResv( id ) {
                    isOver = false
                    resvTR = document.getElementById( id )
                    resvTR.bgColor = ''
                }
                </script>
				<table>
					<tr>
                        <td width="15%%" class="dataCaptionFormat"> <%= _("Photo")%></td>
                        <td width="20%%" class="dataCaptionFormat"> <%= _("Room name")%></td>
                        <td width="15%%" class="dataCaptionFormat"> <%= _("Capacity")%></td>
                        <td width="15%%" class="dataCaptionFormat"> <%= _("Site")%></td>
                        <td width="65%%" class="dataCaptionFormat"> <%= _("Actions")%></td>
					</tr>
					<tr>
						<td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
					</tr>
					<% for room in rooms: %>
					    <% myDetails = detailsUH.getURL( room ) %>
                        <% onClickDetails = 'onclick="window.location=\'%s\'"' % myDetails %>
                        <% bookMe = bookingFormUH.getURL( room ) %>
                        <% modifyMe = urlHandlers.UHRoomBookingRoomForm.getURL( room ) %>
					    <tr style="height: 60px" id="<%= room.id %>" onmouseover="handleMouseOverResv(<%=room.id%>)" onmouseout="handleMouseOutResv(<%=room.id%>)">
					        <td <%=onClickDetails%> >
					            <% if room.photoId != None: %>
					                <img src="<%= room.getSmallPhotoURL() %>" />
					            <% end %>
					        </td>
					        <td <%=onClickDetails%> ><%= room.building %>-<%= room.floor %>-<%= room.roomNr %>
                                <% if room.name != str(room.building) + '-' + str(room.floor) + '-' + str(room.roomNr): %>
                                    <small>(<%= room.name %>)</small>
                                <% end %>
                            </td>
					        <td <%=onClickDetails%> align = 'center'><%= room.capacity %></td>
					        <td <%=onClickDetails%> ><%= room.site %></td>
                            <td>
                                <a href="<%= myDetails %>" > <%= _("view")%></a> <br />
                                <% if room.canBook( user ): %>
                                    <a href="<%= bookMe %>">book</a> <br />
                                <% end %>
                                <% if room.canPrebook( user ) and not room.canBook( user ): %>
                                    <a href="<%= bookMe %>"> <%= _("PRE-book")%></a> <br />
                                <% end %>
                                <% if room.canModify( user ): %>
                                    <a href="<%= modifyMe %>"> <%= _("modify")%></a> <br />
                                <% end %>
                            </td>
					    </tr>
					<% end %>

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

                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br />
