<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2">${ _("Modify an accommodation type")}</td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Caption")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <input type="text" name="caption" size="60" value=${ caption }>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Number of places")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <input type="text" name="placesLimit" size="60" value="${ placesLimit }"> <i>(${ _("use '0' for unlimited")})</i>
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Disable type")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <input type="checkbox" name="cancelled" size="60" ${ checked }>
          </td>
        </tr>
        <tr>
            <td class="titleCellTD"><span class="titleCellFormat">Is Billable</span></td>
            <td bgcolor="white" class="blacktext" width="100%">
              <input type="checkbox" name="billable" size="60" ${ billable }>${ _("(uncheck if it is not billable)") }
            </td>
          </tr>
          <tr>
            <td class="titleCellTD"><span class="titleCellFormat">${ _("Price") }</span></td>
            <td bgcolor="white" class="blacktext" width="100%">
              <input type="text" name="price" size="60" value="${ price }">
            </td>
          </tr>
        <tr>
          <td>&nbsp;</td>
        </tr>
        <tr>
          <td valign="bottom" align="left" colspan="2">
            <input type="submit" class="btn" name="modify" value="${ _("modify")}" style="width:80px">
            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}" style="width:80px">
          </td>
        </tr>
    </table>
</form>