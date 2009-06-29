<table align="center" width="95%%">
    <tr>
        <td class="formTitle"> <%= _("Room Mappers")%></td>
    </tr>
    <tr>
        <td>
            <br>
            <table width="60%%" align="center" border="0" style="border-left: 1px solid #777777">
                <tr>
                    <td colspan="3" class="groupTitle"> <%= _("Room Mapper")%> <font size="+1">%(name)s</font></td>
				</tr>
				<tr>
					<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Description")%></span></td>
					<td bgcolor="white" width="100%%" valign="top" class="blacktext">%(description)s</td>
				</tr>
                <tr>
			        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Map URL")%></span></td>
			        <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(url)s</td>
			    </tr>
                <tr>
			        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Place Name")%></span></td>
			        <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(placeName)s</td>
			    </tr>
                <tr>
			        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Regular expressions")%></span></td>
			        <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(regexps)s</td>
			    </tr>
				<tr>
			        <td colspan="2" align="center">
			            <form action="%(modifyURL)s" method="POST">
			                <input type="submit" class="btn" value="<%= _("modify")%>">
			            </form>
			        </td>
			    </tr>
			</table>
		</td>
	</tr>
</table>
