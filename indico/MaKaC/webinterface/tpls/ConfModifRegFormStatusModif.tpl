<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2">${ _("Modify status")}</td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Caption")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <input type="text" name="caption" size="60" value="${ caption }">
          </td>
        </tr>
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Values")}</span></td>
          <td bgcolor="white" class="blacktext" width="100%">
            <table>
                <tr>
                    <td valign="top"><input type="text" name="newvalue"></td>
                    <td rowspan="2" valign="top" align="left">
                        <input type="submit" class="btn" name="addvalue" value="${ _("add")}"><br>
                        <input type="submit" class="btn" name="removevalue" value="${ _("remove")}"><br>
                        <input type="submit" class="btn" name="defaultvalue" value="${ _("set as default")}"><br>
                    </td>
                </tr>
                <tr><td>${ values }</td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>&nbsp;</td>
        </tr>
        <tr>
          <td valign="bottom" align="left" colspan="2">
            <input type="submit" class="btn" name="save" value="${ _("save")}" style="width:80px">
            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}" style="width:80px">
          </td>
        </tr>
    </table>
</form>
