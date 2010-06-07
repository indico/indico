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

<table width="80%%" class="filesTab">
<tr>
<td>
	<table>
		<tr>
			<td class="groupTitle">
				 <%= _("Existing bookings")%>
			</td>
		</tr>
		<tr>
			<td style="white-space: nowrap;">
				<table>
					<tr>
					  <td class="dataCaptionFormat"><%= _("Photo")%></td>
					  <td class="dataCaptionFormat"><%= _("Room")%></td>
					  <td class="dataCaptionFormat"><%= _("Reason")%> /<br /><%= _("For whom")%></td>
	                  <td class="dataCaptionFormat">
	                    <%= _("Next")%> / <%= _("Period")%>
	                    <% inlineContextHelp( _("First line shows date of the <b>next repetition</b>.<br /><br /> Next lines show booking period, or just booking date for non-repeating bookings.") ) %>
	                  </td>
					  <td class="dataCaptionFormat"><%= _("Hours")%></td>
					  <td class="dataCaptionFormat"><%= _("Actions")%></td>
					</tr>
					<tr>
						<td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
					</tr>
					<%     includeTpl( 'RoomBookingListItem', unrolledReservations = reservations, withPhoto = True ) %>
					<tr>
						<td class="titleCellTD" colspan="10" style="height: 0px">&nbsp;</td>
					</tr>
				</table>
				&nbsp;
			</td>
		</tr>
	</table>
	<br />
	<br />
</td>
</tr>
</table>
