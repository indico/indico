
<table width="100%%" cellspacing="0" align="center" border="0">
    %(filterOptions)s
    <tr>
        <td>
        <table border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td colspan="6">
                    <a name="results"></a>
                    <table width="100%%">
                        <tr>
                            <td nowrap width="100%%"><div class="groupTitle"><%= _("Current registrants")%> (%(numRegistrants)s)</div></td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(imgNameTitle)s<a href=%(urlNameTitle)s><%= _("name")%></a></td>
                <% if regForm.getPersonalData().getDataItem("institution").isEnabled(): %><td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(imgInstitutionTitle)s<a href=%(urlInstitutionTitle)s><%= _("institution")%></a></td><% end %>
                <% if regForm.getPersonalData().getDataItem("position").isEnabled(): %><td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(imgPositionTitle)s<a href=%(urlPositionTitle)s><%= _("position")%></a></td><% end %>
                <% if regForm.getPersonalData().getDataItem("city").isEnabled(): %><td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(imgCityTitle)s<a href=%(urlCityTitle)s><%= _("city")%></a></td><% end %>
                <% if regForm.getPersonalData().getDataItem("country").isEnabled(): %><td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(imgCountryTitle)s<a href=%(urlCountryTitle)s><%= _("country/region")%></a></td><% end %>
                %(sessionsTitle)s
            </tr>
            %(registrants)s
            <tr><td>&nbsp;</td></tr>
            <tr>
                <td colspan="10" valign="bottom" align="left">&nbsp;</td>
            </tr>
        </table>
        </td>
    </tr>
</table>
