
<form action= ${ listOfBookings } method="POST">
<table width="65%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
        <td colspan="3" class="groupTitle"> ${ _("Details of your Booking")}:</td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}:</span></td>
        <td bgcolor="white" width="100%">&nbsp; <b>${ title }</td>
         </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}:</span></td>
        <td bgcolor="white" width="100%">&nbsp; <b>${ description }</td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ }: </span></td>
        <td bgcolor="white" width="100%">&nbsp;  <b>${ starting }</td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Ending")}:</span></td>
        <td bgcolor="white" width="100%">&nbsp;  <b>${ ending }</td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Virtual Room")}: </span></td>
        <td bgcolor="white" width="100%">&nbsp; <b>${ virtualRoom }</font></td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Mailing list")}: </span></td>
        <td bgcolor="white" width="100%">&nbsp; <b>${ supportEmail }</td>
        </tr>
    <tr><td>&nbsp;</td></tr>
        <tr>
       <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Password Protection")}: </span></td>
       <td bgcolor="white" width="100%">&nbsp; <b>${ protectionStatus }</b></td>
    </tr>
        <tr align="center">
        <td colspan="2" valign="bottom" align="center">
        <table align="center">
        <tr>
        <td></td>
        <td><input type="submit" class="btn" value="${ _("Back to Booking List")}"></td>&nbsp;
        </tr>
</table>
</form>
