
<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
            <font size="+1">%(title)s</font>
        </td>
		<form action="%(modifyURL)s" method="POST">
        <td rowspan="5" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(description)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File type")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(typeDesc)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File size")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(fileSize)s</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("File name")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(fileName)s <a href="%(fileAccessURL)s"><img src="%(downloadImg)s" border="0" style="vertical-align:middle" alt="download"></a></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
