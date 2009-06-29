<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Title")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(title)s</td>
		<form action=%(dataModificationURL)s method="POST">
        <td rowspan="3" valign="bottom" align="right">
			<input type="submit" class="btn" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Content")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext"><pre>%(content)s</pre></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
