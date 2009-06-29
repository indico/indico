<table width="100%%">
	<tr>
		<td>
			<form action=%(filterPostURL)s method="POST">
				%(currentSorting)s
				<table width="100%%" align="center" border="0">
					<tr>
						<td class="groupTitle"><%= _("Display options")%></td>
					</tr>
					<tr>
						<td>
							<table width="100%%">
								<tr>
									<td>
										<table align="center" cellspacing="10" width="100%%">
											<tr style="background-color: #ECECEC;">
											%(typeFilterHeader)s
												<td align="center" class="titleCellFormat"> <%= _("show sessions")%></td>
											%(trackFilterHeader)s
											</tr>
											<tr>
											%(types)s
												<td valign="top" style="border-right:1px solid #777777;">%(sessions)s</td>
											%(tracks)s
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
			<table align="center" width="100%%" border="0" cellpadding="0" cellspacing="0">
				<tr>
					<td colspan="9">
                        <a name="contribs"></a>
                        <table cellpadding="0" cellspacing="0">
                            <tr>
                                <td class="groupTitle" width="100%%" style="margin-bottom: 20px;"><%= _("Contribution List")%> (%(numContribs)s)</td>
                                <td nowrap align="right" style="border-bottom: 1px solid #777777;">%(contribSetIndex)s</td>
                            </tr>
                        </table>
                    </td>
				</tr>
				<tr>
					<td colspan="9"><br /><br /></td>
				</tr>
				<tr>
					<td></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> %(numberImg)s<a href=%(numberSortingURL)s> <%= _("Id")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> %(dateImg)s<a href=%(dateSortingURL)s> <%= _("Date")%></a></td>
					%(typeHeader)s
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(titleImg)s<a href=%(titleSortingURL)s> <%= _("Title")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> %(speakerImg)s<a href=%(speakerSortingURL)s> <%= _("Presenter")%></a></td>
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(sessionImg)s<a href=%(sessionSortingURL)s> <%= _("Session")%></a> </td>
					%(trackHeader)s
					<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Files")%></td>
				</tr>
				<form action=%(contribSelectionAction)s method="post" target="_blank">
				%(contributions)s
				<tr>
                    <td colspan="9" align="right">%(contribSetIndex)s</td>
                </tr>
				<tr>
					<td colspan="9" valign="bottom" align="left">
						<input type="submit" class="btn" name="PDF" value="<%= _("booklet of selected contributions")%>" style="width:264px">
					</td>
				</tr>
				</form>
				<tr>
					<form action=%(contributionsPDFURL)s method="post" target="_blank">
					<td colspan="9" valign="bottom" align="left">
							%(contribsToPrint)s
							<input type="submit" class="btn" value="<%= _("booklet of all contributions")%>" style="width:264px">
					</td>
					</form>
				</tr>
				<tr><td colspan="9">&nbsp;</td></tr>
			</table>
		</td>
	</tr>
</table>

