<br>
<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" class="blacktext" width="100%%">%(title)s</td>
		<form action="%(dataModificationURL)s" method="POST">
        <td rowspan="4" valign="bottom" align="right" width="100%%">
			<input type="submit" class="btn" value="<%= _("modify")%>">
		</td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" class="blacktext">
        %(description)s
      </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Place")%></span></td>
        <td bgcolor="white" class="blacktext">%(place)s</td>
    </tr>
    <tr>
        
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Duration")%></span></td>
        <td bgcolor="white" class="blacktext">%(duration)s</td>
    </tr>
    <tr>
        
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Keywords")%></span></td>
        <td bgcolor="white" class="blacktext"><pre>%(keywords)s</pre></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Presenters")%></span></td>
        <td bgcolor="white" class="blacktext" colspan="2">%(speakersTable)s</td>
    </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Report numbers")%></span</td>
        <td bgcolor="white" colspan="2"><i>%(reportNumbersTable)s</i></td>
      </tr>
      <tr>
</table>
<br>
