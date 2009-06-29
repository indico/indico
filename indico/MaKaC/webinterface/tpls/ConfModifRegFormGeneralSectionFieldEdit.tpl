
<script type="text/javascript">
  var saveIsFocused = false;
  var addIsFocused = false;
  function controle(){
    if (saveIsFocused
      && document.WConfModifRegFormGeneralSectionFieldEdit.billable != null
      && document.WConfModifRegFormGeneralSectionFieldEdit.billable.checked == "1"
      && document.WConfModifRegFormGeneralSectionFieldEdit.price.value == ""){
      alert("<%= _("As you checked 'Billable', please enter now a price or uncheck 'Billable'.")%>")
      return false;
    }
    else if (addIsFocused
      && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable != null
      && document.WConfModifRegFormGeneralSectionFieldEdit.newbillable.checked == "1"
      && document.WConfModifRegFormGeneralSectionFieldEdit.newprice.value == ""){
      alert("<%= _("As you checked 'Billable', please enter now a price or uncheck 'Billable'.")%>")
      return false;
    }
    else{
      return true;
    }
  }
</script>

<form id="WConfModifRegFormGeneralSectionFieldEdit" name="WConfModifRegFormGeneralSectionFieldEdit" action=%(postURL)s method="POST" onsubmit="return controle()">
  <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle" colspan="2"> <%= _("Modify general field")%></td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Caption")%></span></td>
      <td bgcolor="white" class="blacktext" width="100%%">
      <input type="text" name="caption" size="60" value=%(caption)s>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Type of field")%></span></td>
      <td bgcolor="white" class="blacktext" width="100%%">
      %(inputtypes)s
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat"> <%= _("Mandatory field")%></span></td>
      <td bgcolor="white" class="blacktext" width="100%%">
      <input type="checkbox" name="mandatory" size="60" %(mandatory)s> ( <%= _("uncheck if it is not a mandatory field")%>)
      </td>
    </tr>

    %(specialOptions)s
  <tr>
      <td>&nbsp;</td>
    </tr>
    <tr>
      <td valign="bottom" align="left" colspan="2">
      <input type="submit" class="btn" name="save" value="<%= _("save")%>" style="width:80px" onFocus="saveIsFocused=true;" onBlur="saveIsFocused=false;">
      <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>" style="width:80px">
      </td>
    </tr>
  </table>
</form>
