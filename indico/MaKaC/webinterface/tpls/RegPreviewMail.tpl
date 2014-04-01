<br>
<table width="80%" align="center" style="border-top:1px solid #777777; border-left:1px solid #777777">
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> ${ _("From")}&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>${ From }</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> ${ _("To")}&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>${ to }</b><br><small><font color="green">( ${ _("This is the preview for only one registrant, but the email will be sent to all the selected registrants")})</font></small></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> ${ _("cc")}&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>${ cc }</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> ${ _("Subject")}&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>${ subject }</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> ${ _("Body")}&nbsp;&nbsp;&nbsp;</td>
        <td width="100%" style="color:black"><pre>${ body | h }</pre></td>
    </tr>
</table>
<br>


    <table width="50%" align="center" border="0">
        <tr>
            <td align="right">
                <form action=${ postURL } method="POST">
                    ${ params }
                    <input type="submit" class="btn" name="OK" value="${ _("send")}">
                    <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                </form>
            </td>
            <td>
                <form action=${ backURL } method="POST">
                    ${ params }
                    <input type="submit" class="btn" name="emailSelected" value="back" />
                </form>
            </td>
        </tr>
    </table>
