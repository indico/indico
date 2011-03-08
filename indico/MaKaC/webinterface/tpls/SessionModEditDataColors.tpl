<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Background Color")}</span></td>
  <td bgcolor="white" width="100%">
    <table>
    <tr>
      <td>
        <input type="text" size="7" name="backgroundColor" value="${ bgcolor }">
    <input name="backgroundColorpreview" type="text" style="background:${ bgcolor }; border:1px solid black;width:20px;" DISABLED>
    <a href="" onClick="javascript:window.open('${ bgcolorChartURL }','color','scrollbars=no,menubar=no,width=330,height=140');return false;"><img style="border:0px;vertical-align:bottom" src="${ colorChartIcon }" alt="Select color"></a>
      </td>
    </tr>
    </table>
  </td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Text Color")}</span></td>
  <td bgcolor="white" width="100%">
    <table>
    <tr>
      <td valign="top">
        <input type="text" size="7" name="textColor" value="${ textcolor }">
    <input name="textColorpreview" type="text" style="background:${ textcolor }; border:1px solid black;width:20px;" DISABLED>
    <a href="" onClick="javascript:window.open('${ textcolorChartURL }','color','scrollbars=no,menubar=no,width=330,height=140');return false;"><img style="border:0px;vertical-align:bottom" src="${ colorChartIcon }" alt="Select color"></a>&nbsp;
      </td>
      <td>
        <input type="checkbox" name="autotextcolor"> ${ _("Automatic text color")}<br>
        <input type="checkbox" name="textcolortolinks" ${ textColorToLinks }> ${ _("Apply text color to links")}
      </td>
    </tr>
    </table>
  </td>
</tr>