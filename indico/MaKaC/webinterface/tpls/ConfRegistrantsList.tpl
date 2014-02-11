<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <p>Number of participants: ${numRegistrants}</p>
    <table cellspacing="0" border="0">
        ${ filterOptions }
        <tr>
            <td>
            <table border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="6">
                        <a name="results"></a>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">${ imgNameTitle }<a href=${ urlNameTitle }>${ _("name")}</a></td>
                    ${'<td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">'+ imgInstitutionTitle +'<a href='+ urlInstitutionTitle +'>'+ _("institution")+'</a></td>' if not regForm.getPersonalData().getField("institution").isDisabled() else ""}
                    ${'<td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">'+ imgPositionTitle +'<a href='+ urlPositionTitle +'>'+ _("position")+'</a></td>' if not regForm.getPersonalData().getField("position").isDisabled() else ""}
                    ${'<td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">'+ imgCityTitle +'<a href='+ urlCityTitle +'>'+ _("city")+'</a></td>' if not regForm.getPersonalData().getField("city").isDisabled() else ""}
                    ${'<td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">'+ imgCountryTitle +'<a href='+ urlCountryTitle +'>'+ _("country/region")+'</a></td>' if not regForm.getPersonalData().getField("country").isDisabled() else ""}
                    ${ sessionsTitle }
                </tr>
                ${ registrants }
                <tr><td>&nbsp;</td></tr>
                <tr>
                    <td colspan="10" valign="bottom" align="left">&nbsp;</td>
                </tr>
            </table>
            </td>
        </tr>
    </table>
</%block>
