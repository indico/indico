<table width="100%" cellspacing="0" align="center" border="0">
    <tr>
       <td nowrap colspan="10">
            <div class="CRLgroupTitleNoBorder">${ _("Attendance Statistics") }
            </div>
        </td>
    </tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr>
        <td valign="top">
        <table border="0">
            <tr>
                <td class="titleCellFormat"> ${ _("Invited participants")} </td>
                <td><strong>${ invited }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${ _("Rejected invitations")} </td>
                <td><strong>${ rejected }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${ _("Added participants")} </td>
                <td><strong>${ added }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${ _("Refused to attend")} </td>
                <td><strong>${ refused }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${ _("Pending participants")} </td>
                <td><strong>${ pending }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${ _("Declined participants")} </td>
                <td><strong>${ declined }</strong></td>
            </tr>
            <tr><td>&nbsp;</td><td>&nbsp</td></tr>
            % if conferenceStarted:
            <tr>
                <td class="titleCellFormat"> ${_("Present participants")} </td>
                <td><strong>${ present }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${_("Absent participants")} </td>
                <td><strong>${ absent }</strong></td>
            </tr>
            <tr>
                <td class="titleCellFormat"> ${_("Excused participants")} </td>
                <td><strong>${ excused }</strong></td>
            </tr>
            %endif
        </table>
        </td>
    </tr>
</table>
<br>
