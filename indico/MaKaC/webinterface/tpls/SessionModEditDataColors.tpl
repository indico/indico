<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Background Color")}</span></td>
  <td bgcolor="white" width="100%">
  <div id="backgroundColorField" class="colorField"></div>
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Text Color")}</span></td>
  <td bgcolor="white" width="100%">
    <div id="textColorField" class="colorField"></div>
  </td>
</tr>
<script type="text/javascript">
    $("#backgroundColorField").html(new ColorPickerWidget("backgroundColor", ${bgcolor.replace("#","") | n, j}).draw());
    $("#textColorField").html(new ColorPickerWidget("textColor", ${textcolor.replace("#","") | n, j}).draw());
</script>
