<table class="regFormSectionTable" width="100%" align="left" cellspacing="0">
    <tr>
        <td nowrap class="regFormSectionTitle" colspan="2">${ title }</td>
    </tr>
    % if description:
    <tr>
        <td align="left" style="padding: 10px 0 5px 15px;" colspan="2">${ description }</td>
    </tr>
    % endif
    <tr>
        <td nowrap style="padding: 10px 0 5px 15px;">
            <span>${ _("Select your preferred choice")}</span>
            <span class="regFormMandatoryField">*</span>
        </td>
        <td width="100%" align="left" style="padding: 10px 0 5px 15px;">${ sessions1 }</td>
    </tr>
    <tr>
        <td nowrap style="padding: 10px 0 5px 15px;">
            <span>${ _("Select your second choice")}</span>
            <span class="regFormItalic">${ _("(Optional)")}</span>
        </td>
        <td width="100%" align="left" style="padding: 10px 0 5px 15px;">${ sessions2 }</td>
    </tr>
</table>
