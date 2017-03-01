<table bgcolor="gray" border="0" width="80%" align="center">
    <tr bgcolor="white">
        <td align="center">
            <br>
            <font size="+3" color="red">-- <u> ${ _("ERROR")}</u> --</font>
            <br><br>
            <table bgcolor="red" width="60%"><tr><td bgcolor="white" align="center">
                <b>${ errorText }</b>
            </td></tr></table>
            <br>
            <table align="center"><tr><td>
                 ${ _("""Please, go back to the previous page using the "back" button of your browser and check the data you fill in<br><br>
                If the problem persist, please, use the following form to send a message to the administrator """)}:<br><br>
                <table bgcolor="gray" align="center"><tr><td bgcolor="white">
                    <table><tr><td width="10"> </td><td>
                    <form action=${ sendReportURL } method="post">
                        <br>
                        <input type="hidden" name="systemComments" value="${ msg }">
                         ${ _("Please, add any comment you think usefull for the administrator to understand the problem")}:<br>
                        <textarea name="comments" rows="10" cols="100"></textarea><br><br>
                         ${ _("Your email address")} : <input type="text" name="email" value="${ email }" size="40"><br><br>
                        <center><input type="submit" class="btn" value="${ _("send the message")}"></center>
                    </form>
                    </td><td width="10"> </td></tr></table>
                </td></tr></table>
                <br>
            </td></tr></table>
        </td>
    </tr>
</table>
