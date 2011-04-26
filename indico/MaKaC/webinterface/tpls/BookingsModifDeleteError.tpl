
<table width="65%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="3" class="groupTitle"> ${ _("Your Booking could not be deleted!")}</td>
        </tr>
        <tr><td>&nbsp;</td></tr>
    <tr>
       <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Reason")}: </span></td>
       <td bgcolor="white" width="100%">&nbsp; <b>${ ErrorReason }</b></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <td>
    <td><form action=${ gobackURL } method="POST"> <input type="Submit" Value=" ${ _("Back to Booking List")}"></form></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
