<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
	<tr>
		<td colspan="2" class="groupTitle"> <%= _("Log Item Details")%></td>
	</tr>
	<tr><td>&nbsp;</td><td>&nbsp;</td></tr>
	<tr>
		<td colspan="2">
		%(errorMsg)s
		%(infoMsg)s
		</td>
	</tr>
	<tr>
		<td>
			<table>
				%(logItem)s
			</table>
		</td>
		<td align="right" valign="top">
		<form action="%(logListAction)s" method="post">
			<input type="submit" class="btn" name="logListButton" value="<%= _("Event Log List")%>">
		</form>
		</td>
	</tr>
</table>

