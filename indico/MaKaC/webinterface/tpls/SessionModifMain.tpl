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
  <td colspan="2">
      <table width="100%">
          <tr>
              <td style="width: 80%"><ul id="inPlaceConveners" class="UIPeopleList"></ul></td>
              <td nowrap valign="top" style="width: 20%; text-align:right;">
                  <span id="inPlaceConvenersMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                      <a class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px" onclick="convenerManager.addManagementMenu();">${ _("Add convener")}</a>
                  </span>
              </td>
          </tr>
       </table>
   </td>
</tr>
<tr>
  <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>
</table>

<script>

var convenerManager = new SessionConvenerManager('${ confId }', {confId: '${ confId }', sessionId: '${ sessionId }'}, $E('inPlaceConveners'), $E('inPlaceConvenersMenu'),
        "convener", ${ conveners | n,j});

</script>
