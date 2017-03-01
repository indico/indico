<%
from indico.util.i18n import _
%>

<div class="container">

<table align="center" width="80%">
    <tr>
        <td align="center"><font size="+2" color="#5294CC"><b> ${ _("Sorry, your request cannot be completed because of an unexpected error on the Indico server.")}</b></font></td>
    </tr>
    <tr>
        <td>
            <table width="90%" align="center">
                <tr>
                    <td>
                        <ul><font size="2" color="#5294CC" >
                            <li>
                                <form target="_blank" action=${ reportURL }
                                    method="post">
                                    <input type="hidden" name="reportMsg" value=${ reportMsg }>
                                    <input type="hidden" name="userEmail" value=${ userEmail }>
                 ${ _("You can notify the Indico support team by using the following button")}: <input type="submit" class="btn" color="blue" value="${ _("Send Error Report")}">
                                </form>
                        </font></ul>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>

${ errorDetails }

</div>
