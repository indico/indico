<% declareTemplate(newTemplateStyle=True) %>

<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName">
            <span>Room name</span>
        </td>
        <td>
            <input id="roomName" type="text" size="60" name="roomName" value="<%= EventTitle %>" />
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;">
            <span>Description</span>
        </td>
        <td>
            <textarea rows="3" cols="60" name="roomDescription"><%= EventDescription %></textarea>
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName">
            <span>Owner</span>
        </td>
        <td>
            <span id="owner"></span>
            <img id="ownerHelpImg" src="<%= systemIcon('help')%>" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName">
            <span>PIN</span>
        </td>
        <td>
            <span id="PINField"></span>
            <img id="PINHelpImg" src="<%= systemIcon('help')%>" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
</table>
