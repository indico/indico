<table width="100%" align="center">
    <tr>
        <td>
			<table align="center" width="95%" border="0">
				<tr>
					<td>
						<table align="center" width="100%" border="0">
							<tr>
								<td colspan="2" align="center"><%= modifyItem %> <td width="100%"><b><font color="black" size="+1"><%= title %></font></b></td>
							</tr>
							<tr>
								<td>&nbsp;</td>
								<td align="center" colspan="2">
									<table width="95%" align="center" border="0">
										<tr>
											<td nowrap class="displayField" valign="top"><b> <%= _("Dates")%>:</b></td>
											<td width="100%"><%= dateInterval %></td>
										</tr>
										<%= material %>
                                        <tr>
                                            <td colspan="2">&nbsp;</td>
                                        </tr>
									</table>
								</td>
							</tr>
						</table>
					</td>
				</tr>
			</table>
		</td>
	</tr>
</table>
<table width="100%">
    <tr>
        <td colspan="3"><%= contribs %></td>
    </tr>
</table>