<form action=${ postURL } method="POST" onsubmit="return parameterManager.check();">
<table width="90%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-bottom: 5px; border-bottom: 1px solid #BBBBBB;">
<tr>
  <td colspan="3" class="groupTitle">${ action } a Field</td>
</tr>
<tr>
  <td nowrap class="titleCellTD" style="padding-top: 10px;"><span class="titleCellFormat"> ${ _("Type")}</span></td>
  <td colspan="2" bgcolor="white" width="100%"  style="padding-top: 10px;">&nbsp;
    <select name="fieldType">
    ${ fieldTypeOptions }
    </select>
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Name")}</span></td>
  <td colspan="2" bgcolor="white" width="100%">&nbsp;
    <input type="hidden" name="fieldId" value=${ id }>
    <input id="nameInput" type="text" name="fieldName" value=${ name } size="60">
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Caption")}</span></td>
  <td colspan="2" bgcolor="white" width="100%">&nbsp;
    <input id="captionInput" type="text" name="fieldCaption" value=${ caption } size="60">
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Max length")}<br>( ${ _("'0' means no restriction")})</span></td>
  <td colspan="2" bgcolor="white" width="100%">&nbsp;
    <input type="text" name="fieldMaxLength" value=${ maxlength } size="4">
    <select name="limitation">
        % if (limitationOption=="words"):
            <option value="words" selected="selected">${_("words")}</option>
            <option value="chars">${_("characters")}</option>
        % else:
            <option value="words">${_("words")}</option>
            <option value="chars" selected="selected">${_("characters")}</option>
        % endif
    </select>
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Mandatory")}</span></td>
  <td colspan="2" bgcolor="white" width="100%">&nbsp;
    <input type="radio" name="fieldIsMandatory" value="Yes" ${ selectedYes }> ${_("Yes")}
    <input type="radio" name="fieldIsMandatory" value="No" ${ selectedNo }> ${_("No")}
  </td>
</tr>
<tr><td colspan="3"><br></td></tr>
<tr align="left">
  <td colspan="3" valign="bottom" align="left">
    <input type="submit" class="btn" name="save" value="${ _("save")}">
    <input type="submit" class="btn" name="cancel" value="${ _("cancel")}" onclick="this.form.onsubmit = function(){ return true;};">
  </td>
</tr>
</table>
</form>

<script>

var parameterManager = new IndicoUtil.parameterManager();
parameterManager.add($E('nameInput'), null, false);
parameterManager.add($E('captionInput'), null, false);

</script>
