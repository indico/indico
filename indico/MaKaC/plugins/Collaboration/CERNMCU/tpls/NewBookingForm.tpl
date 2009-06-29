<% declareTemplate(newTemplateStyle=True) %>

<span><strong>Please input the necessary parameters to book a conference in the CERN MCU</strong></span>

<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName">
            <span>Name</span>
        </td>
        <td>
            <input id="title" type="text" size="60" name="name" value="<%=EventTitle%>" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>Description</span>
        </td>
        <td>
            <textarea rows="5" cols="60" name="description"><%=EventDescription%></textarea>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>ID</span>
        </td>
        <td>
            <input type="radio" id="autoYesRB" name="autoGenerateId" value="yes" onclick="disableCustomId()" checked/>
            <label for="autoYesRB">Let Indico choose</label>
            <input type="radio" id="autoNoRB" name="autoGenerateId" value="no" onclick="enableCustomId()" />
            <label for="autoNoRB">Choose one manually: </label>
            <input type="text" size="10" name="customId" id="customId" disabled />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Start date</span>
        </td>
        <td>
            <input type="text" size="16" name="startDate" value="<%= DefaultStartDate %>" />
            <span class="bookingFormWarning">Please keep the dd/mm/yyyy hh:mm format</span>
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>End date</span>
        </td>
        <td>
            <input type="text" size="16" name="endDate" value="<%= DefaultEndDate %>" />
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
            <span>PIN</span>
        </td>
        <td>
            <input type="password" size="10" name="pin" value="" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;padding-top: 10px;">
            <span>Remote Participants</span>
        </td>
        <td style="padding-top: 10px;" id="participantsCell" class="participantsCell">
        </td>
    </tr>
    
</table>
