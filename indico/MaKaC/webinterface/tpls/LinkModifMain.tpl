<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            <font size="+1">%(title)s</font>
        </td>
		<form action="%(modifyURL)s" method="POST">
        <td rowspan="3" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(description)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("URL")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext"><a href="%(url)s">%(url)s</a></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
