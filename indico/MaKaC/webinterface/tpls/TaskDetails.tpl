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
        <a href="${ conferenceList }"> ${ _("Conference&nbsp;List&nbsp;")}</a>
    </td>
  </tr>

  <tr><td>&nbsp;</td></tr>
  <tr>
    <td class="menutitle" colspan="2">
      ${ taskDetailsTitle }
    </td>
  </tr>
  <tr><td colspan="2">&nbsp;</td></tr>
  <tr>
    <td colspan="2" align="right">
      <a href="${ taskList }"> ${ _("Task&nbsp;List&nbsp;")}</a>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
        <form method="post" action="${ taskDetailsAction }">
        <input type="hidden" name="editRights" value="${ editRights }">
        <table width="70%">
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Task Id")}</span></td>
                <td>
                    &nbsp;${ taskId }
                    <input type="hidden" name="taskId" value="${ taskId }">
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Created by")}</span></td>
                <td>
                    &nbsp;${ createdBy }
                    <input type="hidden" name="createdBy" value="${ creatorId }">
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Title")}
                </span></td>
                <td>&nbsp;${ taskTitle }</td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Status")}
                </span></td>
                <td>
                        <table width="100%">
                        <tr>
                            <td >${ taskStatus }</td>
                            <td align="right">
                                <select name="changedStatus" ${ statusDisabled }>${ taskStatusOptions }</select>
                            </td>
                            <td width="29%">
                                &nbsp;<input type="submit" class="btn" name="performedAction" value="${ _("Change status")}" ${ statusDisabled }>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Description")}
                </span></td>
                <td>${ taskDescription }</td>
            </tr>
            ${ responsible }
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Comments")}
                </span></td>
                <td>
                <table width="100%">
                    <tr>
                        <td>
                            ${ showCommentsButton }
                            ${ showComments }
                        </td>
                        <td width="29%">&nbsp;${ newCommentButton }</td>
                    </tr>
                    <tr>
                        <td colspan="2">${ commentsList }</td>
                    </tr>
                </table>
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                     ${ _("Status history")}
                </span></td>
                <td>
                <table width="100%">
                    <tr>
                        <td>
                            ${ showStatusButton }
                            ${ showStatus }
                        </td>
                    </tr>
                    <tr>
                        <td>${ statusList }</td>
                    </tr>
                </table>
                </td>
            </tr>
            <tr><td>&nbsp;</td></tr>
        </table>
        </form>
    </td>
  </tr>
</table>
