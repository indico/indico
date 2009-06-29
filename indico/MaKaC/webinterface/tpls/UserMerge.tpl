    <table width="95%%" align="center">
      <tr>
        <td class="formTitle"> <%= _("Merge users")%></td>
      </tr>
    </table>
<br><br>
<form action="%(submitURL)s">
    <table width="95%%" align="center">
      <tr>
        <td>
          <input type="submit" name="selectPrin" value="<%= _("Select principal user")%>">
        </td>
        <td>
          <input type="submit" name="selectToMerge" value="<%= _("Select user to merge")%>">
        </td>
      </tr>
      <tr>
        <td>
          &nbsp;
        </td>
      </tr>
      <tr>
        <td width="40%%" valign="top" align="center">
          <table width="10%%">
            <input type="hidden" name="prinId" value="%(prinId)s">
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(ptitle)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Name")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(pname)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("First name")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(pfirstName)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Affiliation")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(porganisation)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(pemail)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Address")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext"><pre>&nbsp;&nbsp;%(paddress)s</pre></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Telephone")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(ptelephone)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Fax")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(pfax)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Logins")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(plogins)s</td>
            </tr>
          </table>
        </td>
        <td width="40%%" style="border-left: 1px solid #777777" valign="top" align="center">
          <table width="10%%">
            <input type="hidden" name="toMergeId" value="%(toMergeId)s">
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Title")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mtitle)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Name")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mname)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("First name")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mfirstName)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Affiliation")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(morganisation)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(memail)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Address")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext"><pre>&nbsp;&nbsp;%(maddress)s</pre></td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Telephone")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mtelephone)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Fax")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mfax)s</td>
            </tr>
            <tr>
              <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Logins")%></span></td>
              <td>&nbsp;</td>
              <td bgcolor="white" width="100%%" valign="top" class="blacktext">%(mlogins)s</td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td>
          &nbsp;
        </td>
      </tr>
      <tr>
        <td colspan="2" align="center">
          <input type="submit" name="merge" value="<%= _("Merge")%>">
        </td>
      </tr>
    </table>
</form>