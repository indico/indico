
<table width="65%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="3" class="groupTitle"> ${ _("Your VRVS Booking has not been created!")}</td>
        </tr>
        <tr><td>&nbsp;</td></tr>
         <tr>
             <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Problem")}: </span></td>
       <td bgcolor="white" width="100%">&nbsp; <b> ${ _("It was impossible to place your booking.")}</b></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
       <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Reason")}: </span></td>
       <td bgcolor="white" width="100%">&nbsp; <b>${ bookingError }</b></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <td>
    <td><b> ${ _("To edit the values entered go \"Back\" in your browser. To go back to the default values, push \"Reset\" button")}</td>
    <td><form action=${ gobackURL } method="POST"> <input type="Submit" Value=" ${ _("Reset")}"></form></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
</table>
