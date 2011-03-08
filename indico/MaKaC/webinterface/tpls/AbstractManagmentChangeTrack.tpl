
<table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2">${ _("Change the track assignment for the abstract")}: <br><span style="letter-spacing: 0px;">"${ abstractName }"<br><br></span></b></font>
        </td>
    </tr>
    <tr>
        <td align="center" bgcolor="white">
            <br>
            <table>
                <tr>
                    <td bgcolor="white">
                        <form action=${ saveURL } method="POST">
                            ${ tracks }
                    </td>
                </tr>
            </table>
            <br>
            <table width="100%" style="border-top: 1px solid #777777">
                <tr>
                    <td bgcolor="white" align="right" valign="bottom">
                            <input type="submit" class="btn" name="save" value="${ _("save")}">
                    </td>
                    </form>
                    <td bgcolor="white" align="left" valign="bottom">
                        <form action=${ cancelURL } method="POST">
                            <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>



</table>
