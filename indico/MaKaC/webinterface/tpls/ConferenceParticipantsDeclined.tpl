<table width="100%" cellspacing="0" align="center" border="0">
    <tr>
       <td nowrap colspan="10">
            <div class="CRLgroupTitleNoBorder">${ _("Displaying")} <span style="font-weight: bold;">${numberDeclined}</span>
                 ${_("declined")} ${ _("participant") if numberDeclined == 1 else _("participants")}
            </div>
        </td>
    </tr>
    <tr id="headDeclined">
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Name")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Affiliation")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Email")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Address")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Telephone")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Fax")}
        </td>
    </tr>
    % for key, d in declined:
        <tr id="declined${key}">
            <td class="CRLabstractDataCell" valign="top">${d.getFullName()}</td>
            <td class="CRLabstractDataCell" valign="top">${d.getAffiliation()}</td>
            <td class="CRLabstractDataCell" valign="top">${d.getEmail()}</td>
            <td class="CRLabstractDataCell" valign="top">${d.getAddress()}</td>
            <td class="CRLabstractDataCell" valign="top">${d.getTelephone()}</td>
            <td class="CRLabstractDataCell" valign="top">${d.getFax()}</td>
        </tr>
    % endfor
</table>