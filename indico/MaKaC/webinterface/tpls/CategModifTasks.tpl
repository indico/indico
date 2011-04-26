
<table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle" colspan="2"> ${ _("Task List Management")}</td>
    </tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Tasks")}</span></td>
      <td bgcolor="white" width="100%" class="blacktext">${ tasksAllowed }</td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
          <td class="groupTitle" colspan="2"> ${ _("Access Control")}</td>
    </tr>
    <form action="${ taskAction }" method="POST">
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Current status")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
        ${ locator }
        <b>${ accessVisibility }</b>
        <small>${ changeAccessVisibility }</small>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Users allowed to access")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
          <table width="100%">
              <tr>
                  <td align="right">
                      <select name="accessChosen">${ accessOptions }</select>
                      <input type="submit" name="taskAccessAction" value="${ _("Add")}">
                      <input type="submit" name="taskAccessAction" value="${ _("New")}">
                      <input type="submit" name="taskAccessAction" value="${ _("Remove")}">
                  </td>
              </tr>
              <tr>
                  <td>
                  ${ accessList }
                  </td>
              </tr>
          </table>
      </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
          <td class="groupTitle" colspan="2"> ${ _("Comment Rights")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Current status")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
        ${ locator }
        <b>${ commentVisibility }</b>
        <small>${ changeCommentVisibility }</small>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Users allowed to comment")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
          <table width="100%">
              <tr>
                  <td align="right">
                      <select name="commentChosen">${ commentOptions }</select>
                      <input type="submit" name="taskCommentAction" value="${ _("Add")}">
                      <input type="submit" name="taskCommentAction" value="${ _("New")}">
                      <input type="submit" name="taskCommentAction" value="${ _("Remove")}">
                  </td>
              </tr>
              <tr>
                  <td>
                  ${ commentList }
                  </td>
              </tr>
          </table>
      </td>
    </tr>

    <tr><td>&nbsp;</td></tr>

    <tr>
          <td class="groupTitle" colspan="2"> ${ _("Modification Control")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Task Managers")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
          <table width="100%">
              <tr>
                  <td align="right">
                      <select name="managerChosen">${ managerOptions }</select>
                      <input type="submit" name="taskManagerAction" value="${ _("Add")}">
                      <input type="submit" name="taskManagerAction" value="${ _("New")}">
                      <input type="submit" name="taskManagerAction" value="${ _("Remove")}">
                  </td>
              </tr>
              <tr>
                  <td>
                  ${ managerList }
                  </td>
              </tr>
          </table>
      </td>
    </tr>
    </form>
    <tr><td>&nbsp;</td></tr>
</table>
