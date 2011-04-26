
<form action=${ postURL } method="POST">
    <input type="hidden" name="toEmails" value="${ emails }">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="3" class="groupTitle">${ _("Send Email")}</font></b>
            </td>
        </tr>
        <tr>
            <td>From: </td>
            <td colspan="2"><input type="text" name="from" size="50" value="${ From }"/></td>
        </tr>
        <tr>
            <td>
                To:
            </td>
            <td colspan="2" style="padding-top:5px; padding-bottom:5px">${ toEmails }</td>
        </tr>
        <tr>
            <td>
                CC:
            </td>
            <td colspan="2" style="padding-top:5px; padding-bottom:5px"><input type="text" name="cc" size="50" value=""/> (comma-separated email addresses)</td>
        </tr>
        <tr>
            <td>Subject:</td>
            <td><input type="text" name="subject" size="64" value="${ subject }"/></td>
            <td align="center" valign="middle" rowspan="2">
        </td>
        </tr>
       <tr>
            <td valign="top">Body:</td>
        <td colspan="2"><textarea name="body" rows="26" cols="50">${ body }</textarea></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="3" align="center">
                <input type="submit" class="btn" name="OK" value="${ _("send")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
