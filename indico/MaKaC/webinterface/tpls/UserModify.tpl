<center>
<form action="%(postURL)s" method="POST">
    %(locator)s
    <table width="80%%">
        <tr>
            <td colspan="2" align="center"><font size="+2"><u>%(Wtitle)s</u></font></td>
        </tr>
            <td colspan="2" align="center">
                <table width="90%%"><tr><td>
                    <font color="gray">
                        <br><br>
                    </font>
                </td></tr></table>
                %(msg)s
            </td>
        </tr>
        <tr>
            <td colspan="2"><b><%= _("Personal data")%></b></td>
        </tr>
        <tr>
            <td colspan="2" bgcolor="black"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><%= _("Title")%><font></td>
            <td align="left">
                <select name="title">
                    %(titles)s
                </select>
            </td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><font color="red">* </font><%= _("Family name")%></font></td>
            <td align="left"><input type="text" name="surName" value="%(surName)s" size="100"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><font color="red">* </font><%= _("First name")%></font></td>
            <td align="left"><input type="text" name="name" value="%(name)s" size="100"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><font color="red">* </font><%= _("Organisation")%></font></td>
            <td align="left"><input type="text" name="organisation" value="%(organisation)s" size="100"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><font color="red">* </font><%= _("Primary email")%></font></td>
            <td align="left"><input type="text" name="email" value="%(email)s" size="100"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><%= _("Secondary emails")%></font></td>
            <td align="left">%(secEmails)s</td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><%= _("Address")%></font></td>
            <td align="left"><textarea name="address" rows="5" cols="75">%(address)s</textarea></td>
        </tr>
        <tr>
            <td align="right" nowrap><font color="gray"><%= _("Telephone number")%></font></td>
            <td align="left"><input type="text" name="telephone" value="%(telephone)s" size="25"></td>
        </tr>
        <tr>
            <td align="right"><font color="gray"><%= _("Fax number")%></font></td>
            <td align="left"><input type="text" name="fax" value="%(fax)s" size="25"></td>
        </tr>
        <tr>
            <td colspan="2">
                <center><font color="red"><%= _("You must enter a valid address. A mail will be sent to you to confirm the registration")%></font></center>
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <br><b><%= _("""All fields with a <font color="red">*</font> must be fill in""")%><br>
                <br><input type="submit" class="btn" name="Save" value="<%= _("confirm")%>"> <input type="submit" class="btn" name="cancel" value="<%= _("Cancel")%>"></td>
        </tr>
    </table>
<br>

</form>
</center>