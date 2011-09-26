<table class="regFormSectionTable" width="100%" align="left" cellspacing="0">
    <tr>
        <td nowrap class="regFormSectionTitle">${ title }</td>
    </tr>
    % if description:
    <tr>
        <td style="padding-left:10px">
            <table width="100%">
                <tr>
                    <td align="left" style="padding: 10px 0 0 5px;"><pre>${ description }</pre></td>
                </tr>
            </table>
        </td>
    </tr>
    % endif
    <tr>
        <td style="padding: 10px 0 0 15px">
            <table align="left">
                <tr>
                    <td align="left">
                        <span>${ _("Arrival date")}</span>
                        <span class="regFormMandatoryField">*</span>
                    </td>
                    <td align="left" style="padding-left: 5px;">${ arrivalDate }</td>
                </tr>
                <tr>
                    <td align="left">
                        <span>${ _("Departure date")}</span>
                        <span class="regFormMandatoryField">*</span>
                    </td>
                    <td align="left" style="padding-left: 5px;">${ departureDate }</td>
                </tr>
            </table>
        </td>
    </tr>
% if accommodationTypes != "":
    <tr>
        <td style="padding: 5px 0 0 15px;">
            <table align="left">
                <tr>
                    <td align="left">
                        <span id="accommodationTypeLabel" class="subGroupTitleRegForm">${ _("Select your accommodation")}</span>
                        <span class="regFormMandatoryField">*</span>
                    </td>
                </tr>
                ${ accommodationTypes }
            </table>
        </td>
    </tr>
% endif
</table>
