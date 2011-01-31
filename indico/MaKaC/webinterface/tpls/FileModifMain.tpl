
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext">
            <font size="+1"><%= title %></font>
        </td>
		<form action="<%= modifyURL %>" method="POST">
        <td rowspan="5" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext"><%= description %></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File type")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext"><%= typeDesc %></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File size")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext"><%= fileSize %></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File name")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext"><%= fileName %> <a href="<%= fileAccessURL %>"><img src="<%= downloadImg %>" border="0" style="vertical-align:middle" alt="download"></a></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>