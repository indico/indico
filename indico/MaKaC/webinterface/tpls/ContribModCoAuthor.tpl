<form action=%(postURL)s method="POST">
    <table width="60%%" align="center" border="0" 
                                    style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"><%= _("Editing a co-author")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Title")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <select name="title">%(titles)s</select>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Family name")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="70" name="surName" value=%(surName)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("First name")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="70" name="name" value=%(name)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Affiliation")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="70" name="affiliation" value=%(affiliation)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Email")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="70" name="email" value=%(email)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Address")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <textarea name="address" rows="5" cols="50">%(address)s</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Telephone")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="25" name="phone" value=%(phone)s>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"><%= _("Fax")%></span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="text" size="25" name="fax" value=%(fax)s>
            </td>
        </tr>
        <tr>
            <td colspan="2">&nbsp;</td>
        </tr>
        <tr>
            <td colspan="2">
                <input type="submit" class="btn" name="ok" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
