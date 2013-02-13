<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Meeting title")}</span>
        </td>
        <td>
            <input id="meetingTitle" type="text" size="60" name="meetingTitle" value="${ EventTitle }" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>${ _("Agenda")}</span>
        </td>
        <td>
            <textarea rows="3" cols="60" name="meetingDescription">${ EventDescription }</textarea>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Timezone")}</span>
        </td>
        <td>
            <span>${ TimeZone }</span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Session")}</span>
        </td>
        <td>
            ${ SessionList }
            <span id="session"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Start time")}</span>
        </td>
        <td>
            <input id="startDate" type="text" size="16" name="startDate" id="startDate" value="${ DefaultStartDate }" />
            <img id="startDateHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Ending time")}</span>
        </td>
        <td>
            <input id="endDate" type="text" size="16" name="endDate" id="endDate" value="${ DefaultEndDate }" />
            <img id="endDateHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("WebEx username")}</span>
        </td>
        <td>
            <input id="webExUser" type="text" size="16" name="webExUser" value="${ DefaultWebExUser }" />
            <img id="webExUserHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("WebEx password")}</span>
        </td>
        <td>
            <input id="webExPass" type="password" size="16" name="webExPass" value="${ DefaultWebExPass }" />
            <img id="webExPassHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Access password")}</span>
        </td>
        <td>
            <input type="password" size="20" name="accessPassword" value="" />
            <img id="passwordHelpImg" src="${ systemIcon('help') }" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;padding-top: 10px;">
            <span>${ _("Invite Attendees")}</span>
        </td>
        <td style="padding-top: 10px;" id="participantsCell">
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>${ _("Email options")}</span>
        </td>
        <td>
<!--            Send email to event managers? <input id="sendCreatorEmail" type="checkbox" name="sendCreatorEmail" value="yes" />-->
           <input id="sendAttendeesEmail" type="hidden" name="sendAttendeesEmail" value="yes" />
           <input id="sendSelfEmail" type="checkbox" name="sendSelfEmail" value="yes" /><input id="loggedInEmail" type="hidden" name="loggedInEmail" value="" /> ${ _("Send a copy of the invitation email to your Indico email account?")}
        </td>
    </tr>

</table>
