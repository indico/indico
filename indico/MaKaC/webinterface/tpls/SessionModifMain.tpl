<table width="95%" border="0">
${ Code }
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
  <td bgcolor="white" class="blacktext">
    ${ title }
  </td>
  <td rowspan="${ Rowspan }" valign="bottom" align="right" width="1%">
    <form action=${ dataModificationURL } method="POST">
    <input type="submit" class="btn" value="${ _("modify")}">
    </form>
  </td>
</tr>
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
  <td bgcolor="white" class="blacktext">
        ${ description }
  </td>
</tr>
<tr>
  <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> ${ _("Default contribution duration")}</span></td>
  <td bgcolor="white" class="blacktext">${ entryDuration }</td>
</tr>
${ Type }
${ Colors }
<tr>
  <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>
</table>
