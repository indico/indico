<br>
<table width="100%%" align="center">
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
			<table align="center" width="65%%" border="0" style="border: 1px solid #777777;">
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td align="center"><font size="+1" color="black"><b> <%= _("Material management")%></b></font></td>
				</tr>
				<tr><td>&nbsp;</td></tr>
				<tr>
					<td>
						<table width="85%%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
							<tr>
								<td class="groupTitle" colspan="2" style="background:#E5E5E5; color:gray" nowrap>&nbsp;&nbsp;&nbsp; <%= _("Modifying link data")%></td>
							</tr>
								<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
								<td align="left"><input type="text" name="title" size="60" value="%(title)s"></td>
							</tr>
							<tr>
								<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
								<td align="left"><textarea name="description" cols="43" rows="6">%(description)s</textarea></td>
							</tr>
							<tr>
								<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Target URL")%></span></td>
								<td align="left"><input type="text" name="url" value="%(url)s"></td>
							</tr>
							<tr><td>&nbsp;</td></tr>
							<tr>
								<td colspan="2" align="left"><input type="submit" class="btn" value="<%= _("ok")%>"></td>
							</tr>
						</table>
					</td>
				</tr>
			</table>
		</td>
	</tr>
</table>



