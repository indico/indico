<table>
    <tr>
        <td class="bookingFormFieldName">
            <span>Name</span>
        </td>
        <td>
            <input id="title" type="text" size="60" name="name" value="${EventTitle}" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>Description</span>
        </td>
        <td>
            <textarea rows="3" cols="60" name="description">${EventDescription}</textarea>
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
            <img id="customIdHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>Start date</span>
        </td>
        <td>
            <input type="text" size="16" name="startDate" value="${ DefaultStartDate }" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>End date</span>
        </td>
        <td>
            <input type="text" size="16" name="endDate" value="${ DefaultEndDate }" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName">
            <span>PIN</span>
        </td>
        <td style="padding-top: 10px;">
            <span id="PINField"></span>
            <img id="PINHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;padding-top: 10px;">
            <span>Remote Participants</span>
        </td>
        <td style="padding-top: 10px;" id="participantsCell">
        </td>
    </tr>

</table>
