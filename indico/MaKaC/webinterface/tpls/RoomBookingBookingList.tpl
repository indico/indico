<% declareTemplate(newTemplateStyle=True) %>

<% def orderBy(text, keyword): %>
<% nParams = rh._reqParams.copy() %>
<% nParams['order'] = keyword %>
<a href="<%= urlHandlers.UHRoomBookingBookingList.getURL( newParams = nParams ) %>"><%= text %></a>
<% end %>

    <table cellpadding="0" cellspacing="0" border="0" width="80%%">
	    <tr>
	    <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%%">&nbsp;</td>
	    </tr>
        <tr>
            <td class="bottomvtab" width="100%%">
                <table width="100%%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">

                            <span class="formTitle" style="border-bottom-width: 0px">
                            <% if not title: %>
                                <!-- Generic title -->
                                <%= len( reservations ) %>  <%= _("Booking(s) found")%>:
                            <% end %>
                            <% if title: %>
                                <%= title + " (" + str(len(reservations)) + ")" %>:
                            <% end %>
                            </span>
                            <% if prebookingsRejected: %>
                                <br /><br />
                                <span class="actionSucceeded"><%= subtitle %></span>
                                <p style="margin-left: 6px;"><%= description %></p>
                            <% end %>
                            <br /><br />

<table width="100%%" class="filesTab">
<tr>
<td>

    <script type="text/javascript">
    isOver = false
    function handleMouseOverResv( id ) {
        if ( isOver )
		{
		 return;
		}
        isOver = true;
        resvTR = document.getElementById( id );
        resvTR.bgColor = '#f0f0f0';
    }
    function handleMouseOutResv( id ) {
        isOver = false;
        resvTR = document.getElementById( id );
        resvTR.bgColor = '';
    }
    </script>

	<% includeTpl( 'RoomBookingBookingListPrevNext' ) %>

    <% if not overload: %>
      	<table style="width: 736px;">
    		<tr>
    		    <td>
                    <div style="margin: 22px 0px 16px 0px;">
                        <% if manyRooms: %>
                            <% includeTpl( 'RoomBookingManyRoomsCalendar' ) %>
                        <% end %>
                        <% else: %>
                            <% includeTpl( 'RoomBookingRoomCalendar', room = room ) %>
                        <% end %>
                    </div>
                </td>
            </tr>
        </table>
        <br /><br />
		<% includeTpl( 'RoomBookingBookingListPrevNext' ) %>
    <% end %>


	<table style="width: 736px;">
		<tr>
    <% if withPhoto: %>
          <% columnNumber = 6 %>
		  <td style="width: 90px;" class="dataCaptionFormat">Photo</td>
    <% end %>
    <% else: %>
          <% columnNumber = 5 %>
    <% end %>
		  <td style="width: 100px;" class="dataCaptionFormat"><% orderBy('Room','room') %></td>
		  <td class="dataCaptionFormat"><% orderBy('Reason','reason') %> / <br /><% orderBy('For whom','for') %></td>
		  <td style="width: 88px;" nowrap class="dataCaptionFormat">
		    <% orderBy('Date','date') %>
		  </td>
		  <td style="width: 46px;" class="dataCaptionFormat" ><% orderBy('Hours', 'hours') %></td>
		  <td style="width: 52px; padding-right: 15px;" class="dataCaptionFormat"><%= _("Actions")%></td>
		</tr>
		<tr>
			<td colspan="<%= columnNumber %>" style="height: 0px;">&nbsp;</td>
		</tr>

        <% if not overload: %>
			<% for collision in unrolledReservations: %>
		    	<% includeTpl( 'RoomBookingListItem', reservation = collision.withReservation, occurrence = collision, withPhoto = withPhoto ) %>
			<% end %>
		<% end %>
		<% if overload: %>
		    <tr><td colspan="<%= columnNumber %>"><strong><br /> <%= _("Too many searching results or too large time span. Please issue more specific query.")%></strong></td></tr>
		<% end %>

        <% if showRejectAllButton: %>
            <tr>
                <td colspan="<%= columnNumber %>" style="text-align: right;">
                <form action="<%= urlHandlers.UHRoomBookingRejectAllConflicting.getURL() %>">
                    <input type="submit" class="btn" value="<%= _("Reject ALL Conflicting PRE-Bookings")%>"
                        onclick="if ( !confirm(  <%= _("'Are you sure you want to REJECT ALL conflicting PRE-bookings?'")%> ) ) return false;" />
                </form>
                </td>
            </tr>
        <% end %>

		<tr>
			<td colspan="<%= columnNumber %>" style="height: 0px">&nbsp;</td>
		</tr>
		<tr>
		    <td colspan="<%= columnNumber %>">
		    <% if title and 'My ' in title: %>
		        <b> <%= _("Note")%>:</b>  <%= _("""Your bookings and pre-bookings from <b>old CRBS</b> are not shown on this list.
		        You will see here only bookings done in Indico.
		        To see your old bookings, you must click 'View Bookings' option and find them manually.""")%>
		    <% end %>
		    </td>
		</tr>
	</table>

	<% includeTpl( 'RoomBookingBookingListPrevNext' ) %>


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
