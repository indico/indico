<% declareTemplate(newTemplateStyle=True) %>

<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName">
            <span>Meeting title</span>
        </td>
        <td>
            <input id="meetingTitle" type="text" size="60" name="meetingTitle" value="<%=EventTitle%>" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>Agenda</span>
        </td>
        <td>
            <textarea rows="3" cols="60" name="meetingDescription"><%=EventDescription%></textarea>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Timezone</span>
        </td>
        <td>
            <span><%= TimeZone %></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Session</span>
        </td>
        <td>
            <%= SessionList %>
            <span id="session"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Start time</span>
        </td>
        <td>
            <input id="startDate" type="text" size="16" name="startDate" value="<%= DefaultStartDate %>" />
            <span id="startDateHelp"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Ending time</span>
        </td>
        <td>
            <input id="endDate" type="text" size="16" name="endDate" value="<%= DefaultEndDate %>" />
            <span id="endDateHelp"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>WebEx username</span>
        </td>
        <td>
            <input id="webExUser" type="text" size="16" name="webExUser" value="<%= DefaultWebExUser %>" />
            <span id="WebExUsernameHelp"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>WebEx password</span>
        </td>
        <td>
            <input id="webExPass" type="password" size="16" name="webExPass" value="<%= DefaultWebExPass %>" />
            <span id="WebExPasswordHelp"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Access password</span>
        </td>
        <td>
            <input type="password" size="20" name="accessPassword" value="" />
            <span id="passwordHelp"></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;padding-top: 10px;">
            <span>Attendees</span>
        </td>
        <td style="padding-top: 10px;" id="participantsCell">
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Send email to attendees?</span>
        </td>
        <td>
            <input id="sendAttendeesEmail" type="checkbox" size="16" name="sendAttendeesEmail" value="yes" checked />
        </td>
    </tr>

</table>
