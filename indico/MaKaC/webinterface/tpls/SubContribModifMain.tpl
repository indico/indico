<br>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
        <td bgcolor="white" class="blacktext" width="100%"><%= title %></td>
		<form action="<%= dataModificationURL %>" method="POST">
        <td rowspan="4" valign="bottom" align="right" width="100%">
			<input type="submit" class="btn" value="<%= _("modify")%>">
		</td>
		</form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Description")%></span></td>
        <td bgcolor="white" class="blacktext">
        <%= description %>
      </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Place")%></span></td>
        <td bgcolor="white" class="blacktext"><%= place %></td>
    </tr>
    <tr>

        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Duration")%></span></td>
        <td bgcolor="white" class="blacktext"><%= duration %></td>
    </tr>
    <tr>

        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Keywords")%></span></td>
        <td bgcolor="white" class="blacktext"><pre><%= keywords %></pre></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Presenters")%></span></td>
        <td bgcolor="white" class="blacktext" colspan="2"><%= speakersTable %></td>
    </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Report numbers")%></span</td>
        <td bgcolor="white" colspan="2"><i><%= reportNumbersTable %></i></td>
      </tr>
      <tr>
</table>
<br>