
<table align="center" width="100%%">
    <tr>
       <td class="groupTitle"> <%= _("List of participants")%></td>
    </tr>
	<tr>
		<td>
			<br>
				<table width="100%%" align="center" border="0">
					<tr>
						<td colspan="2" class="groupSubTitle" width="100%%"> <%= _("Submitters")%></td>
					</tr>
					<tr>
						<td width="100%%">
							<table width="100%%">
							%(submitters)s
							</table>
						</td>
						<td align="right" valign="top">
							<form action="mailto:%(submitterEmails)s" method="POST" enctype="text/plain">
								<input type="submit" class="btn" value="<%= _("compose email")%>">
							</form>
							%(showSubmitters)s
						</td>
					</tr>
				</table>
		</td>
	</tr>
	<tr>
		<td>
			<br>
	            <table width="100%%" align="center" border="0">
		            <tr>
						<td colspan="2" class="groupSubTitle" width="100%%"> <%= _("Primary authors")%></td>
					</tr>
					<tr>
						<td width="100%%">
							<table width="100%%">
							%(primaryAuthors)s
							</table>
						</td>
						<td align="right" valign="top">
							<form action="mailto:%(primaryAuthorEmails)s" method="POST" enctype="text/plain">
								<input type="submit" class="btn" value="<%= _("compose email")%>">
							</form>
							%(showPrimaryAuthors)s
						</td>
					</tr>
				</table>
		</td>
	</tr>
	<tr>
		<td>
			<br>
	            <table width="100%%" align="center" border="0">
		            <tr>
						<td colspan="2" class="groupSubTitle" width="100%%"> <%= _("Co-Authors")%></td>
					</tr>
					<tr>
						<td width="100%%">
							<table width="100%%">
							%(coAuthors)s
							</table>
						</td>
						<td align="right" valign="top">
							<form action="mailto:%(coAuthorEmails)s" method="POST" enctype="text/plain">
								<input type="submit" class="btn" value="<%= _("compose email")%>">
							</form>
							%(showCoAuthors)s
						</td>
					</tr>
				</table>
		</td>
	</tr>
</table>