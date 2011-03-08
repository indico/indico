
<br>
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td valign="bottom">
        <span class="categorytitle">${ name }</span>
        <span class="categoryManagers">${ managers }</span>
    </td>
  </tr>
  <tr>
    <td class="subtitle" width="100%">
      ${ description }
    </td>
    <td class="subtitle">
        <a href="${ conferenceList }">${ _("Conference&nbsp;List")}</a>
    </td>
  </tr>

  <tr><td>&nbsp;</td></tr>
  <tr>
    <td class="menutitle" colspan="2">
      ${ taskDetailsTitle }
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
        <form method="post" action="${ taskDetailsAction }">
        <table width="60%">
            <tr><td>&nbsp;</td></tr>
            ${ id }
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Created by")}</span></td>
                <td>
                    ${ createdBy }
                    <input type="hidden" name="createdBy" value="${ creatorId }">
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Title")}
                </span></td>
                <td>
                    <input type="text" name="title" size="86" value="${ title }">
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Description")}
                </span></td>
                <td><textarea name="taskDescription" cols="65" rows="10">${ taskDescription }</textarea></td>
            </tr>
            ${ responsible }
            <tr><td>&nbsp;</td></tr>
            <tr align="center">
                <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
                    <table align="center">
                        <tr>
                            <td><input type="submit" class="btn" value="${ _("ok")}" name="performedAction"></td>
                            <td><input type="submit" class="btn" value="${ _("cancel")}" name="cancel"></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        </form>
    </td>
  </tr>
</table>
