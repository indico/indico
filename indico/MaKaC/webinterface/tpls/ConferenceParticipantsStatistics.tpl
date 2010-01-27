<table width="90%%" align="center" border="0" cellpadding="0" cellspacing="0">
	<tr>
		<td colspan="2" class="groupTitle"> <%= _("Attendance Statistics of")%> %(confTitle)s</td>
	</tr>
	<tr><td>&nbsp;</td><td>&nbsp;</td></tr>
	<tr>
		<td valign="top">
		<table border="0">
			<tr>
				<td class="titleCellFormat"> <%= _("Invited participants")%> </td>
				<td><b>%(invited)s<b></td>
			</tr>
			<tr>
				<td class="titleCellFormat"> <%= _("Rejected invitations")%> </td>
				<td><b>%(rejected)s</b></td>
			</tr>
			<tr>
				<td class="titleCellFormat"> <%= _("Added participants")%> </td>
				<td><b>%(added)s</b></td>
			</tr>
			<tr>
				<td class="titleCellFormat"> <%= _("Refused to attend")%> </td>
				<td><b>%(refused)s<b></td>
			</tr>
			<tr>
				<td class="titleCellFormat"> <%= _("Pending participants")%> </td>
				<td><b>%(pending)s</b></td>
			</tr>
			<tr><td>&nbsp;</td><td>&nbsp</td></tr>
		
			%(present)s
			%(absent)s
			%(excused)s
		</table>
		</td>
	</tr>
</table>
<br>

