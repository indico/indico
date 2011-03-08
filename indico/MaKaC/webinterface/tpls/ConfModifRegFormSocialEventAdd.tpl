<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2">${ _("Add a new social event")}</td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Caption")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <input type="text" name="caption" size="60">
          </td>
        </tr>
        <tr>
          <td>&nbsp;</td>
        </tr>
        <tr>
          <td valign="bottom" align="left" colspan="2">
            <input type="submit" class="btn" name="create" value="${ _("create")}" style="width:80px">
            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}" style="width:80px">
          </td>
        </tr>
    </table>
</form>