<br>
<table width="100%" align="center">
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
			<table align="center" width="65%" border="0" style="border: 1px solid #777777;">
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td align="center"><font size="+1" color="black"><b> <%= _("Material management")%></b></font></td>
				</tr>
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td>
						<table width="90%" align="left" border="0">
							<tr>
								<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
								<td bgcolor="white" width="100%" class="blacktext">
									<font size="+1"><%= title %></font>
								</td>
								<form action="<%= modifyURL %>" method="POST">
								<td rowspan="3" valign="bottom" align="right">
									<input type="submit" class="btn" value="<%= _("modify")%>">
								</td>
								</form>
							</tr>
							<tr>
								<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
								<td bgcolor="white" width="100%" class="blacktext"><%= description %></td>
							</tr>
							<tr>
								<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("URL")%></span></td>
								<td bgcolor="white" width="100%" class="blacktext"><%= url %></td>
							</tr>
							<tr>
								<td colspan="3" class="horizontalLine">&nbsp;</td>
							</tr>
						</table>
					</td>
				</tr>
			</table>
		</td>
	</tr>
</table>


