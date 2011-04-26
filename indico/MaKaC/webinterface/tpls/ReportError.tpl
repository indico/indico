<form action=${ postURL } method="post">
    <input type="hidden" name="reportMsg" value=${ reportMsg }>
    <table align="center">
        <tr>
            <td align="center"><font size="+2" color="#5294CC"><b> ${ _("Error Report Form")}</b></font></td>
        </tr>
        <tr>
            <td align="center"><font size="+1" color="#3366AA"> ${ _("The error you received will be reported to the system developers so they can investigate it.")}<br> ${ _("If required, please enter some additional information and click on \"send report\".")}</font>
            </td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td><table align="center">
                    <tr>
                        <td align="right" valign="top"><font color="#3366AA"> ${ _("additional comments")}</font></td>
                        <td><textarea name="comments" rows="10" cols="50"></textarea></td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"><font color="#3366AA"> ${ _("your email address")}</font></td>
                        <td><input type="text" size="60" name="userEmail" value=${ dstEmail }></td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td align="center"><input type="submit" class="btn" name="confirm" value="${ _("Send Report")}"></td>
        </tr>
    </table>
</form>
