
<script type="text/javascript">
  var saveIsFocused = false;
  var addIsFocused = false;
  var pricePattern = /^\d+([\.]\d+)?$/;
  function controle(){
    if (saveIsFocused
        && document.WConfModifRegFormGeneralSectionFieldEdit.billable != null
        && document.WConfModifRegFormGeneralSectionFieldEdit.billable.checked == "1"
        && document.WConfModifRegFormGeneralSectionFieldEdit.price.value == "") {
            new AlertPopup($T("Warning"), $T("As you checked 'Billable', please enter now a price or uncheck 'Billable'.")).open();
            return false;
    } else if (saveIsFocused
        && document.WConfModifRegFormGeneralSectionFieldEdit.billable != null
        && document.WConfModifRegFormGeneralSectionFieldEdit.billable.checked == "1"
        && !pricePattern.test(document.WConfModifRegFormGeneralSectionFieldEdit.price.value)) {
            new AlertPopup($T("Warning"), $T("Please enter a valid price, only a number.")).open();
            return false;
    } else if (addIsFocused
        && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable != null
        && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable.checked == "1"
        && document.WConfModifRegFormGeneralSectionFieldEdit.newprice.value == "") {
            new AlertPopup($T("Warning"), $T("As you checked 'Billable', please enter now a price or uncheck 'Billable'.")).open();
            return false;
    } else if (addIsFocused
        && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable != null
        && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable.checked == "1"
        && !pricePattern.test(document.WConfModifRegFormGeneralSectionFieldEdit.newprice.value)) {
            new AlertPopup($T("Warning"), $T("Please enter a valid price, only a number.")).open();
            return false;
    } else {
        return true;
    }
  }
</script>

<form id="WConfModifRegFormGeneralSectionFieldEdit" name="WConfModifRegFormGeneralSectionFieldEdit" action=${ postURL } method="POST" onsubmit="return controle();">
  <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle" colspan="2"> ${ _("Modify general field")}</td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Caption")}</span></td>
      <td bgcolor="white" class="blacktext" width="100%">
      <input type="text" name="caption" size="60" value=${ caption } />
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Type of field")}</span></td>
      <td bgcolor="white" class="blacktext" width="100%">
      ${ inputtypes }
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
      <td bgcolor="white" class="blacktext" width="100%">
        <textarea name="description" rows="4" cols="30">${ description }</textarea>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Mandatory field")}</span></td>
      <td bgcolor="white" class="blacktext" width="100%">
      <input type="checkbox" name="mandatory" size="60" ${ mandatory } ${ 'disabled="disabled"' if mandatoryLocked else '' }> ( ${ _("uncheck if it is not a mandatory field")})
      </td>
    </tr>

    ${ specialOptions }
  <tr>
      <td>&nbsp;</td>
    </tr>
    <tr>
      <td valign="bottom" align="left" colspan="2">
      <input id="submitButton" type="submit" class="btn" name="save" value="${ _("save")}" style="width:80px" onFocus="saveIsFocused=true;" onBlur="saveIsFocused=false;">
      <input id="cancelButton" type="submit" class="btn" name="cancel" value="${ _("cancel")}" style="width:80px">
      </td>
    </tr>
  </table>
</form>
