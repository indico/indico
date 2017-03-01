<div class="container">

<table align="center" width="100%">
    <tr>
        <td align="center"><font size="+2" color="#5294CC"><b> ${ _("Your request could not be completed")}:</b></font></td>
    </tr>
    <tr>
        <td>
            <table width="90%" align="center">
                <tr>
                    <td><br>
            <table border ="0" cellpadding="4" cellspacing="1"
                                width="100%">
                 <tr>
                                <td bgcolor="#E5E5E5"><center><b><font size="+1" color="#3366AA">${ area }${ msg }</font></b></center></td>
                            </tr>
                        </table>
                  </td>
                </tr>
                <tr>
                    <td><br></td>
                </tr>
                <tr>
                    <td>
                        <ul><font size="2" color="#5294CC" >
                            <li> ${ _("""You can go back to the precedent page by using the "Back" button of your browser.""")}
                            <li> ${ _("""You can try to refresh this page by using the "Refresh" button of your browser.""")}
                            <li>
                                <form target="_blank" action=${reportURL} method="post">
                                    <input type="hidden" name="reportMsg" value=${reportMsg}>
                                    <input type="hidden" name="userEmail" value=${userEmail}>
                 ${ _("If the problem is not meaningful for you and persists, please notify the Indico support team by sending an error report.")}<br><br>         <center><input type="submit" class="btn" color="blue" value="${ _("Send Error Report")}"> </center>
                                </form>
                        </font></ul>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>

${errorDetails}

</div>
