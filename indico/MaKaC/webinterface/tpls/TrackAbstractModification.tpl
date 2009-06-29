<table width="90%%" border="0" style="border-right:1px solid #777777">
	<tr>
		<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Abstract ID")%></td>
		<td bgcolor="white">%(abstractId)s</td>
		<td align="right">
			<table border="0" cellspacing="1" cellpadding="0">
				<tr>
					<td align="right">
						<a href=%(abstractPDF)s target="_blank"><img src=%(printIconURL)s alt="<%= _("print the current abstract")%>" border="0"> </a>
					</td>
				</tr>
			</table>
		</td>
	</tr>
	<tr>
		<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
					<td bgcolor="white" width="90%%">
						<table width="100%%"><tr>
							<td><b>%(title)s</b></td>
						</tr></table>
					</td>
				</tr> 
                %(additionalFields)s
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Primary authors")%></span></td>
					<td bgcolor="white" valign="top">%(primary_authors)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Co-authors")%></span></td>
					<td bgcolor="white" valign="top">%(co_authors)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Presenters")%></span></td>
					<td bgcolor="white" valign="top"><i>%(speakers)s</i></td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contribution type")%></span></td>
					<td bgcolor="white" valign="top">%(type)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Track classification")%></span></td>
					<td bgcolor="white" valign="top">%(tracks)s</td>
				</tr>
				<tr>
					<td colspan="3" class="horizontalLine">&nbsp;</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Status")%></span></td>
					<td colspan="2" valign="top" bgcolor="%(statusColor)s">
						<table width="100%%">
							<tr>
								<td width="100%%">%(statusDetails)s</td>
								<td align="right" valign="bottom">
									<table align="right">
										<tr>
											<form action=%(proposeToAccURL)s method="POST">
											<td align="right">
													%(proposeToAcceptButton)s
											</td>
											</form>
										</tr>
										<tr>
											<form action=%(proposeToRejURL)s method="POST">
											<td align="right">
													%(proposeToRejectButton)s
											</td>
											</form>
										</tr>
										<tr>
											<form action=%(proposeForOtherTracksURL)s method="POST">
											<td align="right">
													%(proposeForOtherTracksButton)s
											</td>
											</form>
										</tr>
										<tr>
                                            <form action=%(duplicatedURL)s method="POST">
                                            <td align="right">
                                                    %(duplicatedButton)s
                                            </td>
                                            </form>
										</tr>
									</table>
								</td>
							</tr>
							<tr>
								<td colspan="2">%(statusComment)s</td>
							</tr>
						</table>
					</td>
				</tr>
				<tr>
					<td colspan="3" class="horizontalLine">&nbsp;</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Submitted by")%></span></td>
					<td bgcolor="white" valign="top">%(submitter)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Submitted on")%></span></td>
					<td bgcolor="white" valign="top">%(submissionDate)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Last modified on")%></span></td>
					<td bgcolor="white" valign="top">%(modificationDate)s</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Comments")%></span></td>
					<td bgcolor="white" valign="top"><pre>%(comments)s</pre></td>
				</tr>
				<tr>
					<td colspan="3" class="horizontalLine">&nbsp;</td>
				</tr>
				<tr>
					<td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Contribution")%></span></td>
					<td bgcolor="white" valign="top" colspan="3"><pre>%(contribution)s</pre></td>
				</tr>
				<tr>
					<td colspan="3" class="horizontalLine">&nbsp;</td>
				</tr>
			</table>
		</td>
	</tr>
</table>
<br>

