<script type="text/javascript">
<!--
function selectAll()
{
    //document.pendingForm.trackShowNoValue.checked=true
    if (!document.pendingForm.pending.length){
        document.pendingForm.pending.checked=true
    } else {
        for (i = 0; i < document.pendingForm.pending.length; i++) {
            document.pendingForm.pending[i].checked=true
        }
    }
}

function deselectAll()
{
    //document.pendingForm.trackShowNoValue.checked=false
    if (!document.pendingForm.pending.length)    {
        document.pendingForm.pending.checked=false
    } else {
       for (i = 0; i < document.pendingForm.pending.length; i++) {
           document.pendingForm.pending[i].checked=false
       }
    }
}
//-->
</script>

<h2 class="bannerTitle">${ _("List of Pending Participants")}</h2>

<p>
    ${ _("This is a list of persons who have applied for participation in this event")}
</p>

${ errorMsg }
${ infoMsg }

<form action="${ pendingAction }" method="post" name="pendingForm">
    <table>
        <tr>
            <td class="titleCellFormat">
                <img src="${ selectAll }" alt="${ _("Select all")}" onclick="javascript:selectAll()">
                <img src="${ deselectAll }" alt="${ _("Deselect all")}" onclick="javascript:deselectAll()">
                &nbsp;${ _("Name")}
            </td>
            <td class="titleCellFormat">&nbsp;${ _("Status")}</td>
        </tr>
        % for (key, p) in pending:
            <% url = urlHandlers.UHConfModifParticipantsPendingDetails.getURL(conf) %>
            <% url.addParam("pendingId",key) %>
            <tr>
                <td valign="top" class="abstractDataCell">
                    <input type="checkbox" name="pending" value="${ key }" />&nbsp;
                    <a href="${ url }">${ p.getTitle() }&nbsp;${ p.getFirstName() }&nbsp;${ p.getFamilyName() }</a>
                </td>
                <td valign="top" class="abstractDataCell">&nbsp;&nbsp;${ p.getStatus() }</td>
            </tr>
        % endfor
    </table>
    % if not conferenceStarted :
        <div style="margin-top: 20px;">
            <input type="submit" class="btn" value="${ _("Accept selected")}" name="pendingAction" style="margin-right: 20px;"/>
            <input type="submit" class="btn" value="${ _("Reject selected")}" name="pendingAction" />
            <select name="emailNotification">
                <option value="yes" selected>${ _("with email notification")}</option>
                <option value="no">${ _("without email notification")}</option>
            </select>
        </div>
    % endif
</form>

