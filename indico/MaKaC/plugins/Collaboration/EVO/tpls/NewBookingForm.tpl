<table>
    <tr>
        <td class="bookingFormFieldName">
            <span>Community</span>
        </td>
        <td>
            <select name="communityId">
                <option value="chooseOne">-- Choose one --</option>
                % for k,v in Communities:
                <option value="${k}">${v}</option>
                % endfor
            </select>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Meeting title</span>
        </td>
        <td>
            <input id="meetingTitle" type="text" size="60" name="meetingTitle" value="${EventTitle}" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>Description</span>
        </td>
        <td>
            <textarea rows="3" cols="60" name="meetingDescription">${EventDescription}</textarea>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Start time</span>
        </td>
        <td>
            <input id="startDate" type="text" size="16" name="startDate" value="${ DefaultStartDate }" />
            <img id="startDateHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Ending time</span>
        </td>
        <td>
            <input id="endDate" type="text" size="16" name="endDate" value="${ DefaultEndDate }" />
            <img id="endDateHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName">
            <span>Access password</span>
        </td>
        <td>
            <span id="passwordField"></span>
            <img id="passwordHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
</table>
<!--
<div>
<input type="checkbox" id="sendMailCB" name="sendMailToManagers" value="sendMailToManagers"/><label for="sendMailCB">Send a mail notification to all event managers</label>
</div>
 -->
