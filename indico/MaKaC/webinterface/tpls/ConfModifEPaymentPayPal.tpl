
<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">%(title)s</td>
		<form action=%(dataModificationURL)s method="POST">
        <td rowspan="3" valign="bottom" align="right">
			<input type="submit" value="<%= _("modify")%>">
        </td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("URL of PayPal")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext"><pre>%(url)s</pre></td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("business")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext"><pre>%(business)s</pre></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
