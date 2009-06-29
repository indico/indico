<br>
<table width="80%%" align="center" style="border-top:1px solid #777777; border-left:1px solid #777777">
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("From")%>&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>%(from)s</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("To")%>&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>%(to)s</b><br><small><font color="green">( <%= _("This is the preview for only one registrant, but the email will be sent to all the selected registrants")%>)</font></small></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("cc")%>&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>%(cc)s</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Subject")%>&nbsp;&nbsp;&nbsp;</td>
        <td style="color: black"><b>%(subject)s</b></span></td>
    </tr>
    <tr>
        <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Body")%>&nbsp;&nbsp;&nbsp;</td>
        <td width="100%%" style="color:black"><pre>%(body)s</pre></td>
    </tr>
</table>
<br>
<form action=%(postURL)s method="POST">    
    %(params)s
    <table width="80%%" align="center" border="0">
        <tr>
            <td colspan="3" align="center">
                <input type="submit" class="btn" name="OK" value="<%= _("send")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
