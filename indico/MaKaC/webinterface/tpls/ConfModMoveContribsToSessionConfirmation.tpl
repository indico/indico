
<form action=${ postURL } method="POST">
    ${ contributions }
    <input type="hidden" name="targetSession" value=${ targetSessionId }>
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2" style="text-align:center"><img style="vertical-align:middle" src=${ systemIconWarning } border="0" alt="warning">  ${ _("CONFIRMATION")} <img style="vertical-align:middle" src=${ systemIconWarning } border="0" alt="warning"></td>
        </tr>
        <tr>
            <td align="left" colspan="2" bgcolor="white" style="padding-bottom:10px">
                 ${ _("You have selected to move the contributions with ids")}:
                    <p>
                        <b>${ contribIdList }</b>
                    </p>
                 ${ _("to the session")} <i>${ targetSession }</i>.<br><br>
                 ${ _("But there are some <font color='red'>WARNINGS</font>")}:
                <table width="100%">
                    ${ warnings }
                </table>
                <br>
                 ${ _("Please confirm what to do")}:
            </td>
        </tr>
        <tr>
            <td style="border-bottom:1px solid #777777; padding-top:10px" align="center">
                <input type="submit" class="btn" name="CONFIRM" value="${ _("move only those not affected by warnings")}">&nbsp;&nbsp;
                <input type="submit" class="btn" name="CONFIRM_ALL" value="${ _("move all (despite the warnings)")}">&nbsp;&nbsp;
                <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
