<table width="100%">
	<tr>
		<td>
			<form action=<%= filterPostURL %> method="POST">
				<%= currentSorting %>
				<table width="100%" align="center" border="0">
					<tr>
						<td class="groupTitle"><%= _("Display options")%></td>
					</tr>
					<tr>
						<td>
							<table width="100%">
								<tr>
									<td>
										<table align="center" cellspacing="10" width="100%">
											<tr style="background-color: #ECECEC;">
											<%= typeFilterHeader %>
												<td align="center" class="titleCellFormat"> <%= _("show sessions")%></td>
											<%= trackFilterHeader %>
											</tr>
											<tr>
											<%= types %>
												<td valign="top" style="border-right:1px solid #777777;"><%= sessions %></td>
											<%= tracks %>
											</tr>
										</table>
									</td>
								</tr>
								<tr>
									<td align="center" style="background-color: #ECECEC; padding:5px; margin: 10px 0 30px 0; display: block"><input type="submit" class="btn" name="OK" value="<%= _("apply")%>"></input></td>
								</tr>
							</table>
						</td>
					</tr>
				</table>
			</form>
		</td>
	</tr>
	<tr>
		<td>
			<a name="contributions"></a>
			<table align="center" width="100%" border="0" cellpadding="0" cellspacing="0">
				<tr>
					<td colspan="9">
                        <a name="contribs"></a>
                        <table cellpadding="0" cellspacing="0">
                            <tr>
                                <td class="groupTitle" width="100%" style="margin-bottom: 20px;"><%= _("Contribution List")%> (<%= numContribs %>)</td>
                                <td nowrap align="right" style="border-bottom: 1px solid #777777;"><%= contribSetIndex %></td>
                            </tr>
                        </table>
                    </td>
				</tr>
				<tr>
					<td colspan="9"><br /><br /></td>
				</tr>
				<tr>
					<td></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= numberImg %><a href=<%= numberSortingURL %>> <%= _("Id")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= dateImg %><a href=<%= dateSortingURL %>> <%= _("Date")%></a></td>
					<%= typeHeader %>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= titleImg %><a href=<%= titleSortingURL %>> <%= _("Title")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= speakerImg %><a href=<%= speakerSortingURL %>> <%= _("Presenter")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= sessionImg %><a href=<%= sessionSortingURL %>> <%= _("Session")%></a> </td>
					<%= trackHeader %>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Files")%></td>
				</tr>
				<form action=<%= contribSelectionAction %> method="post" target="_blank">
				<%= contributions %>
				<tr>
                    <td colspan="9" align="right"><%= contribSetIndex %></td>
                </tr>
				<tr>
					<td colspan="9" valign="bottom" align="left">
						<input type="submit" class="btn" name="PDF" value="<%= _("booklet of selected contributions")%>" style="width:264px">
					</td>
				</tr>
				</form>
				<tr>
					<form action=<%= contributionsPDFURL %> method="post" target="_blank">
					<td colspan="9" valign="bottom" align="left">
							<%= contribsToPrint %>
							<input type="submit" class="btn" value="<%= _("booklet of all contributions")%>" style="width:264px">
					</td>
					</form>
				</tr>
				<tr><td colspan="9">&nbsp;</td></tr>
			</table>
		</td>
	</tr>
</table>
