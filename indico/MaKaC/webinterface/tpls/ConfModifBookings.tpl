<table align="center" width="100%" class="VCTab"><tr><td>
<table align="center">
    <form action=${ bookSystemURL } method="post">
    <tr>
        <td>
            <a  style="vertical-align:middle"> <font color="gray"></a> <b> ${ _("Please select the system or resource where you want to place the booking")}</b>
        </td>
        ${ bookingSystems }
       <td align="left">
        <input type="submit" class="btn" value="${ _("Create Booking")}">
        </td>
     </tr>
     </form>
     <tr>${ listOfBookings }</tr>
</table>
</td></tr></table>
