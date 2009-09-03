<form action=%(postURL)s method="POST">
<table width="90%%" cellspacing="0" align="center" border="0" style="padding-left:2px; padding-bottom: 5px; border-bottom: 1px solid #BBBBBB;">
<tr>
  <td colspan="3" class="groupTitle">%(action)s  a Field</td>
</tr>
%(errors)s
<tr>
  <td nowrap class="titleCellTD" style="padding-top: 10px;"><span class="titleCellFormat"> <%= _("Type")%></span></td>
  <td colspan="2" bgcolor="white" width="100%%"  style="padding-top: 10px;">&nbsp;
    <select name="fieldType">
    %(fieldTypeOptions)s
    </select>
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Name")%></span></td>
  <td colspan="2" bgcolor="white" width="100%%">&nbsp;
    <input type="hidden" name="fieldId" value=%(id)s>
    <input type="text" name="fieldName" value=%(name)s size="60">
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Caption")%></span></td>
  <td colspan="2" bgcolor="white" width="100%%">&nbsp;
    <input type="text" name="fieldCaption" value=%(caption)s size="60">
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Max Length")%><br>( <%= _("'0' means no restriction")%>)</span></td>
  <td colspan="2" bgcolor="white" width="100%%">&nbsp;
    <input type="text" name="fieldMaxLength" value=%(maxlength)s size="4">
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Mandatory")%></span></td>
  <td colspan="2" bgcolor="white" width="100%%">&nbsp;
    <input type="radio" name="fieldIsMandatory" value="Yes" %(selectedYes)s> Yes
    <input type="radio" name="fieldIsMandatory" value="No" %(selectedNo)s> No
  </td>
</tr>
<tr><td colspan="3"><br></td></tr>
<tr align="left">
  <td colspan="3" valign="bottom" align="left">
    <input type="submit" class="btn" name="save" value="<%= _("save")%>"> 
    <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
  </td>
</tr>
</table>
</form>


