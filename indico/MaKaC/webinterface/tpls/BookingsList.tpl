
<br>
<form action=${ actionPostURL } method="post">
<table width="90%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="10" class="groupTitle"> ${ _("Current Bookings Found")} (${ numBookings })</td>
    </tr>
    <tr>
        <td></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Title")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Description")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Starts")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Ends")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Type")}</td>
    </tr>
    ${ bookings }
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="10" style="border-top:2px solid #777777;padding-top:5px" valign="bottom" align="left">&nbsp;</td>
    </tr>
    <tr>
        <td colspan="10" valign="bottom" align="left">
        <input type="submit" class="btn" name="deleteBookings" value="${ _("delete selected")}"></form>
        </td>
    </tr>
</table>
