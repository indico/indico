<table width="100%">
    <tr>
        <td colspan="2" align="center"><font size="+2"><u>${ _("Creating a new Indico user account")}</u></font></td>
    </tr>
    <tr>
       <td align="center">
            <font size="+1"> ${ _("We found an existing user with the same email address")} :</font><br><br>
            <table bgcolor="gray">
                <tr>
                    <td bgcolor="white">
                        <center><b>&nbsp;${ title } ${ name } ${ surName }&nbsp;</b></center>
                        <b>&nbsp; ${ _("Email")} : </b>${ email }&nbsp;
                    </td>
                </tr>
            </table>
            <br><br>
             ${ _("If you are this person, please use your existing account.")}<br>
             ${ _("If you can't remember your login and password, please use the button below to receive your account name and a link to reset your password by email.")}<br>
            <form action="${ postURL }" method="POST">
                <input type="submit" class="btn" value="${ _("Send My Login Details")}">
            </form>
            <br>
            <br>
             ${ _("If you are not this person, but it is your email address, please contact us")} <a href="mailto:${ contactEmail }"> ${ _("here")}</a>.
       </td>
    </tr>
</table>
