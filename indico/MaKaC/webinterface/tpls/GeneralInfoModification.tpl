<% from indico.util.i18n import getLocaleDisplayNames %>
<form action="${ postURL }" method="POST">
<table width="95%" align="center" border="0">
<tr>
  <td colspan="2" width="100%" class="formTitle">${ _("General admin data")}</td>
</tr>
<tr>
  <td>
    <br>
    <table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td colspan="2" class="groupTitle">${ _("Modify System General Information")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("System title")}</span></td>
      <td bgcolor="white" width="100%">&nbsp;
        <input type="text" size="50" name="title" value="${ title }">
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Organisation/Institution")}</span></td>
      <td bgcolor="white" width="100%">&nbsp;
        <input type="text" size="50" name="organisation" value="${ organisation }">
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Language")}</span></td>
      <td bgcolor="white" width="100%">&nbsp;
         <select name="lang">
           % for l in getLocaleDisplayNames():
           <option ${"selected" if l[0] == language else ""} value="${ l[0] }">${ l[1] }</option>
           % endfor
         </select>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Timezone")}</span></td>
      <td bgcolor="white" width="50%">&nbsp;
           <select name="timezone">${ timezone }</select>
      </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Address")}</span></td>
      <td bgcolor="white" width="100%">
        <table width="100%">
        <tr>
          <td align="right">&nbsp;${ _("City")}</td>
          <td width="100%"><input type="text" name="city" value="${ city }"></td>
        </tr>
        <tr>
          <td align="right">&nbsp;${ _("Country")}</td>
          <td><input type="text" name="country" value="${ country }"></td>
        </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td colspan="2" align="center">
        <table align="center">
        <tr>
          <td>
            <input type="submit" class="btn" name="action" value="${ _("ok")}">
          </td>
          <td>
            <input type="submit" class="btn" name="action" value="${ _("cancel")}">
          </td>
        </tr>
        </table>
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
</form>
