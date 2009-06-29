
<table width="100%%" align="center">
	<tr>
		<td align="center">
			<table align="center">
				<tr>
					<form action=%(modifyURL)s method="POST">
					<td>
						<input type="submit" class="btn" value="<%= _("modify")%>" %(btnModifyDisabled)s>
					</td>
					</form>
					<form action=%(withdrawURL)s method="POST">
					<td>
						<input type="submit" class="btn" value="<%= _("withdraw")%>" %(btnWithdrawDisabled)s>
					</td>
					</form>
					%(btnRecover)s
				</tr>
			</table>
		</td>
	</tr>
    <tr>
        <td>
            <table width="95%%" style="border:1px solid #777777;" cellspacing="1" align="center">
             <tr>
                    <td bgcolor="white">
                        <table width="90%%" align="center">
                            <tr>
                                <td align="center">
                                    <font size="+1" color="black"><b>%(title)s</b></font>
                                </td>
                            </tr>
			    <tr><td>&nbsp;</td></tr>
                            <tr>
                                <td><br></td>
                            </tr>
                            <tr>
                                <td>
                                    <table width="90%%" align="center">
                                        <tr>
                                            <td>
                                                <table width="100%%" cellspacing="0">
                                                    <tr>
                                                        <td nowrap class="displayField"><b> <%= _("Abstract ID")%> :</b></td>
                                                        <td width="100%%">%(abstractId)s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
           %(additionalFields)s
                                        <tr>
                                            <td>
                                                <table width="100%%" cellspacing="0">
                                                    <tr>
                                                        <td nowrap class="displayField" valign="top"><b> <%= _("Primary authors")%> :</b></td>
                                                        <td width="100%%">%(primary_authors)s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <table width="100%%" cellspacing="0">
                                                    <tr>
                                                        <td nowrap class="displayField" valign="top"><b> <%= _("Co-Authors")%> :</b></td>
                                                        <td width="100%%">%(authors)s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><table width="100%%" cellspacing="0">
                                                    <tr>
                                                        <td nowrap class="displayField" valign="top"><b> <%= _("Presenters")%> :</b></td>
                                                        <td width="100%%">%(speakers)s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
											<td>
												<table width="100%%" cellspacing="0">
                                                    <tr>
														<td nowrap class="displayField" valign="top"><b> <%= _("Track classification")%> :</b></td>
														<td width="100%%">%(tracks)s</td>
													</tr>
												</table>
											</td>
                                        </tr>
                                        %(contribType)s
                                        <tr>
                                            <td>
                                                <table cellspacing="0">
                                                    <tr>
                                                        <td nowrap class="displayField" valign="top"><b> <%= _("Submitted by")%> :</b></td>
                                                        <td>%(submitter)s</td>
                                                    </tr>
                                                </table>
											</td>
                                        </tr>
                                        <tr>
											<td>
												<table width="100%%" cellspacing="0">
                                                    <tr>
														<td nowrap class="displayField" valign="top"><b> <%= _("Submitted on")%> :</b></td>
														<td width="100%%">%(submissionDate)s</td>
													</tr>
												</table>
											</td>
                                        </tr>
                                        <tr>
											<td>
												<table width="100%%" cellspacing="0">
                                                    <tr>
														<td nowrap class="displayField" valign="top"><b> <%= _("Last modified on")%> :</b></td>
														<td width="100%%">%(modificationDate)s</td>
													</tr>
												</table>
											</td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <table>
                                                    <tr>
                                                        <td nowrap class="displayField" valign="top"><b> <%= _("Status")%> :</b></td>
                                                        <td>%(status)s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
												<table cellspacing="0">
													<tr>
														<td nowrap class="displayField" valign="top"><b> <%= _("Comments")%> :</b></td>
													</tr>
													<tr>
														<td width="30"></td>
														<td><pre>%(comments)s</pre></td>
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
        </td>
    </tr>
	<tr>
		<td align="center">
			<table align="center">
				<tr>
					<form action=%(modifyURL)s method="POST">
					<td>
						<input type="submit" class="btn" value="<%= _("modify")%>" %(btnModifyDisabled)s>
					</td>
					</form>
					<form action=%(withdrawURL)s method="POST">
					<td>
						<input type="submit" class="btn" value="<%= _("withdraw")%>" %(btnWithdrawDisabled)s>
					</td>
					</form>
					%(btnRecover)s
				</tr>
			</table>
		</td>
	</tr>
</table>
<br>

