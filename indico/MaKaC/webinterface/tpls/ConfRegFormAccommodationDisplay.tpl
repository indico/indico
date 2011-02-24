<table id="regFormSectAccommodation" width="100%%" align="left" class="regSection" cellspacing="0">
    <tr>
        <td nowrap class="groupTitle regSectionBackground"><b>%(title)s</b></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td style="padding-left:10px">
            <table width="100%%">
                <tr>
                    <td align="left"><pre style="white-space:normal">%(description)s</pre></td>
                </tr>
                <tr>
                    <td align="left">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding-left:10px">
            <table align="left">
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font><%= _("Arrival date")%>:</td>
                    <td align="left">&nbsp; %(arrivalDate)s</td>
                </tr>
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font><%= _("Departure date")%>:</td>
                    <td align="left">&nbsp;%(departureDate)s</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
<% if accommodationTypes != "": %>
    <tr>
        <td style="padding-left:10px">
            <table align="left">
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font><span id="accommodationTypeLabel" style="font-weight: bold;"><%= _("Select your accommodation")%>:</span></td>
                </tr>
                %(accommodationTypes)s
            </table>
        </td>
    </tr>
<%end%>
</table>
