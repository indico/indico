<% declareTemplate(newTemplateStyle=True) %>

<span><strong>Please input the necessary parameters to perform an EVO booking</strong></span>

<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName">
            <span>Community name</span>
        </td>
        <td>
            <select name="communityId">
                <% for k,v in Communities.items(): %>
                <option value="<%=k%>"><%=v%></option>
                <% end %>
            </select>
        </td>
    </tr>
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
            <span>Description</span>
        </td>
        <td>
            <textarea rows="10" cols="60" name="meetingDescription"><%=EventDescription%></textarea>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Start time</span>
        </td>
        <td>
            <input id="startDate" type="text" size="16" name="startDate" value="<%= DefaultStartDate %>" />
            <span class="bookingFormWarning">Please keep the dd/mm/yyyy hh:mm format</span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Ending time</span>
        </td>
        <td>
            <input id="endDate" type="text" size="16" name="endDate" value="<%= DefaultEndDate %>" />
            <span class="bookingFormWarning">Please keep the dd/mm/yyyy hh:mm format</span>
        </td>
    </tr>
    <tr>
        <td>
        </td>
        <td>
            <span>Please create your booking between <%= MinStartDate %> and <%= MaxEndDate %></span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Meeting access password</span>
        </td>
        <td>
            <input type="password" size="20" name="accessPassword" value="" />
        </td>
    </tr>
</table>
<div>
<input type="checkbox" id="sendMailCB" name="sendMailToManagers" value="sendMailToManagers"/><label for="sendMailCB">Send a mail notification to all event managers</label>
</div>
