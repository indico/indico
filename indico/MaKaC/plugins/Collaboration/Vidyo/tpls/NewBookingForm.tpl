<div class="redWarningPopup" style="display:none">
${_(" Please be aware that if you modify any sensitive data such as the room name, moderator or PIN that it will be reflected in other bookings which use the same Vidyo room.")}
</div>
<table style="margin-top: 10px;">
    <tr>
        <td class="bookingFormFieldName" nowrap>
            <span>${_("Room name")}</span>
        </td>
        <td>
            <input id="roomName" type="text" size="55" name="roomName" value="${ EventTitle }" />
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;" nowrap>
            <span>${_("Description")}</span>
        </td>
        <td>
            <textarea rows="3" cols="55" name="roomDescription">${ EventDescription }</textarea>
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName" style="vertical-align: top;" nowrap>
            <span>${_("Event linking")}</span>
        </td>
        <td>
            <div id="videoEventLinkType"></div>
            <div id="videoEventLinkSelection"  style="padding-left: 25px;">
                <select id="dummy" disabled="disabled">
                    <option>${_("Default association")}</option>
                </select>
            </div>
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName" nowrap>
            <span>${_("Moderator")}</span>
        </td>
        <td>
            <span id="owner"></span>
            <img id="ownerHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>

    <tr>
        <td class="bookingFormFieldName" nowrap>
            <span>${_("PIN")}</span>
        </td>
        <td>
            <span id="PINField"></span>
            <img id="PINHelpImg" src="${ systemIcon('help')}" style="margin-left:5px; vertical-align:middle;" />
        </td>
    </tr>
</table>
