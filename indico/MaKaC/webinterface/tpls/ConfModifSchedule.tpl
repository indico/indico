<script type="text/javascript">
<!--
function selectAll()
{
  //document.entriesForm.trackShowNoValue.checked=true
  if (!document.entriesForm.entries.length){
  document.entriesForm.entries.checked=true
  } else {
  for (i = 0; i < document.entriesForm.entries.length; i++) {
    document.entriesForm.entries[i].checked=true
    }
  }
}

function deselectAll()
{
  //document.entriesForm.trackShowNoValue.checked=false
  if (!document.entriesForm.entries.length)  {
    document.entriesForm.entries.checked=false
  } else {
   for (i = 0; i < document.entriesForm.entries.length; i++) {
     document.entriesForm.entries[i].checked=false
     }
  }
}
//-->
</script>

<table width="90%" align="center" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
  <tr>
  <td colspan="5" width="90%">
  ${ pdfButton }<br/>
  <table>
    <tr>
    <td width="90%">
    <form action=${ standardAction } method="post">
      <span class="titleCellFormat">&nbsp;${ _("View mode")}</span>
          <select name="view">
          ${ views }
          </select>
          <input type="submit" class="btn" value="${ _("switch")}">
       </form>
      </td>
    </tr>
  </table>
    </td>

  </tr>

  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Start date")}</span></td>
    <td class="blacktext" colspan="3">${ start_date }</td>
    <form action=${ editURL } method="POST">
    <td><input type="submit" class="btn" value="${ _("modify")}"></td>
    </form>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("End date")}</span></td>
    <td class="blacktext" colspan="3">${ end_date }</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Timezone")}</span></td>
    <td bgcolor="white" class="blacktext" colspan="3">${ timezone }</td>
  </tr>
  <tr>
    <td colspan="5" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
  <td colspan="5" class="groupTitle">${ _("List of Scheduled Elements")}</td>
  </tr>
  <tr><td colspan="5">&nbsp;</td></tr>
  <tr><form action=${ fullAction } method="post">
    <td colspan="3"> </td>
    <td width="5%">
      <input type=submit value="${ _("Expand All")}" />
  </td>
  </form>
  <form action=${ entriesAction } method="post" name="entriesForm">
  <td width="5%">
    ${ removeButton }
  </td>
  </tr>
  <tr><td colspan="5">&nbsp;</td></tr>
  <tr>
  <td colspan="5">
  <table width="100%" border="0">
  <tr>
    <td width="4%" class="titleCellFormat" style="border-right:1px solid #FFFFFF;border-left:1px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
    <img src="${ selectAll }" border="0" alt="${ _("Select all")}" onclick="javascript:selectAll()">
    <img src="${ deselectAll }" border="0" alt="${ _("Deselect all")}" onclick="javascript:deselectAll()">
    </td>
    <td width="8%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">&nbsp;${ _("Start")}</td>
    <td width="8%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">&nbsp;${ _("End")}</td>
    <td width="10%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">&nbsp;${ _("Type")}</td>
    <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">&nbsp;${ _("Scheduled Element")}</td>
    <td width="10%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">&nbsp;</td>
  </tr>
    ${ entries }
  </table>
  </form>
  </td>
  </tr>
</table>
<br>
