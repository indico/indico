<table width="95%%" border="0">
%(Code)s
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Title")%></span></td>
  <td bgcolor="white" class="blacktext">
    %(title)s
  </td>
  <td rowspan="%(Rowspan)s" valign="bottom" align="right" width="1%%">
    <form action=%(dataModificationURL)s method="POST">
    <input type="submit" class="btn" value="<%= _("modify")%>">
    </form>
  </td>
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
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Start date")%></span></td>
  <td bgcolor="white" class="blacktext">%(startDate)s</td>
</tr>
<tr>
  <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> <%= _("End date")%></span></td>
  <td bgcolor="white" class="blacktext">%(endDate)s</td>
</tr>
<tr>
  <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> <%= _("Contribution duration")%></span></td>
  <td bgcolor="white" class="blacktext">%(entryDuration)s</td>
</tr>
%(Type)s
%(Colors)s
<tr>
  <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Conveners")%></span></td>
  <form action=%(remConvenersURL)s method="POST">
  <td colspan="2">
  <table width="100%%"><tr>
  <td bgcolor="white" valign="top" class="blacktext">
    %(conveners)s
  </td>
  <td align="right" valign="bottom">
    <table>
    <tr>
      <td>
        <input type="submit" class="btn" value="<%= _("remove")%>">
      </td>
      </form>
      <form action=%(newConvenerURL)s method="POST">
      <td>
        <input type="submit" class="btn" value="<%= _("new")%>">
      </td>
      </form>
      <form action=%(searchConvenerURL)s method="POST">
      <td>
        <input type="submit" class="btn" value="<%= _("search")%>">
      </td>
      </form>
    </tr>
    </table>
  </td>
  </tr></table>
  </td>
</tr>
<tr>
  <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>
</table>            
