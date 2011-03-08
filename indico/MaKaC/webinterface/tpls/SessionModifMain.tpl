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
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default place")}</span></td>
  <td bgcolor="white" class="blacktext">${ place }</td>
</tr>
<!--
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Start date")}</span></td>
  <td bgcolor="white" class="blacktext">${ startDate }</td>
</tr>
<tr>
  <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> ${ _("End date")}</span></td>
  <td bgcolor="white" class="blacktext">${ endDate }</td>
</tr>
-->
<tr>
  <td class="dataCaptionTD"nowrap><span class="dataCaptionFormat"> ${ _("Default contribution duration")}</span></td>
  <td bgcolor="white" class="blacktext">${ entryDuration }</td>
</tr>
${ Type }
${ Colors }
<tr>
  <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>
<tr>
  <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default conveners")}</span></td>
  <form action=${ remConvenersURL } method="POST">
  <td colspan="2">
  <table width="100%"><tr>
  <td bgcolor="white" valign="top" class="blacktext">
    ${ conveners }
  </td>
  <td align="right" valign="bottom">
    <table>
    <tr>
      <td>
        <input type="submit" class="btn" value="${ _("remove")}">
      </td>
      </form>
      <form action=${ newConvenerURL } method="POST">
      <td>
        <input type="submit" class="btn" value="${ _("new")}">
      </td>
      </form>
      <form action=${ searchConvenerURL } method="POST">
      <td>
        <input type="submit" class="btn" value="${ _("search")}">
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