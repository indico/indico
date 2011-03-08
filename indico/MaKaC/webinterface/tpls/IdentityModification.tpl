
<form action="${ postURL }" method="POST">
    ${ locator }
  <table class="groupTable">
    <tr>
        <td colspan="2" class="formTitle"> ${ _("User details")}</td>
    </tr>
    <tr>
      <td colspan="2">
        <br>
        <table width="60%" align="center" border="0" style="border-left: 1px solid #777777">
          <tr>
            <td colspan="3" class="groupTitle">${ WTitle }</td>
          </tr>
          <tr>
            <td colspan="3" bgcolor="white" width="100%" valign="top" style="color:red;padding-top:10px;padding-bottom:10px">${ msg }</td>
          </tr>
          <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("User Name")}</span></td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                &nbsp;&nbsp;
                <input type="text" name="login" value="${ login }" size="40" ${ disabledLogin }>
                ${ hiddenLogin }
            </td>
          </tr>
          <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Password")}</td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<input type="password" name="password" value="" size="40"></td>
          </tr>
          <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Password (again)")}</td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<input type="password" name="passwordBis" value="" size="40"></td>
          </tr>
          <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("System")}</td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<select name="system" ${ disabledSystem }>
              ${ systemList }
            </td>
          </tr>
          <tr>
            <td align="center" colspan="2">
                <input type="submit" class="btn" name="OK" value="${ _("ok")}">
                <input type="submit" class="btn" name="Cancel" value="${ _("Cancel")}">
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</form>